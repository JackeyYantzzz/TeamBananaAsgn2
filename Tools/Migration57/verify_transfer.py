import unreal,pathlib,json,traceback,re,math,runpy,hashlib
P=pathlib.Path(unreal.Paths.project_dir()).resolve()
assert P.name=='场景地图新版'
assert unreal.SystemLibrary.get_engine_version().startswith('5.7.')
S=json.loads((P/'SourceAssets/UE58Transfer/source_snapshot.json').read_text(encoding='utf-8'))
FLAGS=json.loads((P/'SourceAssets/UE58Transfer/actor_collision_flags.json').read_text(encoding='utf-8'))
REPORT={'passed':False,'engine':unreal.SystemLibrary.get_engine_version(),'checks':0,'failures':[],'measurements':{}}
NUMBER=re.compile(r'(?<![A-Za-z_])-?\d+(?:\.\d+)?(?:e[+-]?\d+)?',re.I)

def encode(v):
    if v is None or isinstance(v,(bool,int,float,str)):return v
    if isinstance(v,unreal.Object):return {'object':v.get_path_name()}
    if isinstance(v,unreal.StructBase):return {'struct':type(v).__name__,'text':v.export_text()}
    if isinstance(v,(list,tuple,unreal.Array)):return [encode(x) for x in v]
    if hasattr(v,'name'):return {'enum':type(v).__name__,'name':v.name}
    return str(v)

def equivalent(a,b):
    if a==b:return True
    if isinstance(a,(int,float)) and isinstance(b,(int,float)):return math.isclose(a,b,abs_tol=.001,rel_tol=1e-6)
    if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(equivalent(x,y) for x,y in zip(a,b))
    if isinstance(a,dict) and isinstance(b,dict):
        if a.keys()!=b.keys():return False
        if 'struct' in a:
            if a['struct']!=b['struct']:return False
            aa,bb=a['text'],b['text']
            return NUMBER.sub('#',aa)==NUMBER.sub('#',bb) and equivalent([float(x) for x in NUMBER.findall(aa)],[float(x) for x in NUMBER.findall(bb)])
        return all(equivalent(a[k],b[k]) for k in a)
    return False

def check(name,ok,detail=None):
    REPORT['checks']+=1
    if not ok:REPORT['failures'].append({'name':name,'detail':detail})

def properties(obj,spec,prefix):
    for key,expected in spec.items():
        actual=encode(obj.get_editor_property(key))
        check(prefix+'.'+key,equivalent(actual,expected),{'expected':expected,'actual':actual} if not equivalent(actual,expected) else None)

try:
    for entry in S['assets']:
        obj=unreal.load_asset(entry['path']);check('Asset exists: '+entry['path'],obj is not None)
        assert obj,entry['path']
        check('Asset class: '+entry['path'],obj.get_class().get_name()==entry['class'])
        properties(obj,entry['properties'],entry['path'])
        if entry['class']=='Texture2D':
            filename=pathlib.Path(obj.get_editor_property('asset_import_data').get_first_filename()).resolve()
            check('Texture imports from target project: '+entry['path'],filename.is_relative_to(P))
            expected=P/pathlib.Path(entry['source_file']).relative_to(pathlib.Path(S['source']))
            check('Texture source original bytes: '+entry['path'],hashlib.sha256(filename.read_bytes()).hexdigest()==hashlib.sha256(expected.read_bytes()).hexdigest())
        if entry['class']=='PaperTileMap':
            layers=obj.get_editor_property('tile_layers')
            check('Tile layer count',len(layers)==len(entry['layers']))
            for layer,expected in zip(layers,entry['layers']):properties(layer,expected,'Layer '+expected['layer_name'])
    actors=list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    by_label={a.get_actor_label():a for a in actors}
    check('Same actor labels',set(by_label)=={a['label'] for a in S['actors']})
    for item in S['actors']:
        actor=by_label[item['label']];cls=item['class']
        check(item['label']+' class',actor.get_class().get_name()==cls)
        check(item['label']+' actor collision flag',actor.get_actor_enable_collision()==FLAGS[item['label']])
        check(item['label']+' transform',equivalent(encode(actor.get_actor_transform()),item['transform']))
        check(item['label']+' folder',str(actor.get_folder_path())==item['folder'])
        check(item['label']+' tags',encode(actor.tags)==item['tags'])
        cc={'PaperSpriteActor':unreal.PaperSpriteComponent,'PaperTileMapActor':unreal.PaperTileMapComponent,'PaperGroupedSpriteActor':unreal.PaperGroupedSpriteComponent,'CameraActor':unreal.CameraComponent}[cls]
        c=actor.get_component_by_class(cc);properties(c,item['component'],item['label'])
        if cls!='CameraActor':
            check(item['label']+' collision profile',str(c.get_collision_profile_name())==item['collision_profile'])
            check(item['label']+' collision enabled',encode(c.get_collision_enabled())==item['collision_enabled'])
        if cls=='PaperSpriteActor':check(item['label']+' sprite',encode(c.get_sprite())==item['sprite'])
        elif cls=='PaperGroupedSpriteActor':check(item['label']+' instances',equivalent(encode(c.get_editor_property('per_instance_sprite_data')),item['instances']))
        elif cls=='PaperTileMapActor':
            check('Saved editable tilemap reference',encode(c.get_editor_property('tile_map'))==item['tile_map'] and not c.owns_tile_map())
            w,h,n=c.get_map_size()
            mismatches=[]
            for z in range(n):
                for i,expected in enumerate(item['cells'][z]):
                    actual=c.get_tile(i%w,i//w,z)
                    source_tile=unreal.PaperTileInfo();assert source_tile.import_text(expected['text'])
                    actual_set=actual.get_editor_property('tile_set')
                    source_set=source_tile.get_editor_property('tile_set')
                    # Unreal's empty cells may use 0 or -1; without a tile set both are empty.
                    if actual_set is None and source_set is None:continue
                    if encode(actual)!=expected:mismatches.append([i%w,i//w,z])
            check('Every tile matches source',not mismatches,mismatches[:20])
            REPORT['measurements']['tile_cells_compared']=w*h*n
    runpy.run_path(str(P/'Tools/ReferenceMap/verify_reference_map.py'))
    geometry=json.loads((P/'Saved/reference_map_verified.json').read_text(encoding='utf-8'))
    check('Geometry, collision and original artwork audit',geometry['passed'],geometry['failures'])
    REPORT['measurements'].update({'assets':len(S['assets']),'actors':len(actors),'original_map_checks':geometry['check_count'],'span_cm':12000})
    REPORT['passed']=not REPORT['failures']
    editor=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    camera=by_label['Camera_Reference_Overview']
    editor.pilot_level_actor(camera)
    editor.set_exact_camera_view(True)
    editor.editor_set_game_view(True)
except Exception:REPORT['failures'].append({'exception':traceback.format_exc()})
finally:
    folder=P/'Verification';folder.mkdir(exist_ok=True)
    (folder/'UE57_transfer_verified.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2),encoding='utf-8')
    unreal.log('UE57_TRANSFER_VERIFIED '+str(REPORT['passed']))
