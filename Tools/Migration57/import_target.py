import unreal,pathlib,json,traceback
P=pathlib.Path('C:/Users/dee04/OneDrive/文档/Unreal Projects/场景地图新版')
assert pathlib.Path(unreal.Paths.project_dir()).resolve()==P.resolve()
assert unreal.SystemLibrary.get_engine_version().startswith('5.7.')
S=json.loads((P/'SourceAssets/UE58Transfer/source_snapshot.json').read_text(encoding='utf-8'))
AT=unreal.AssetToolsHelpers.get_asset_tools()
EA=unreal.EditorAssetLibrary
AS=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
REPORT={'success':False,'engine':unreal.SystemLibrary.get_engine_version(),'assets':[],'actors':[]}

def decode(v):
    if isinstance(v,list): return [decode(x) for x in v]
    if not isinstance(v,dict):return v
    if 'object' in v:
        obj=unreal.load_asset(v['object']);assert obj,'Missing asset '+v['object'];return obj
    if 'enum' in v:return getattr(getattr(unreal,v['enum']),v['name'])
    if 'struct' in v:
        obj=getattr(unreal,v['struct'])();assert obj.import_text(v['text']),v;return obj
    raise TypeError(v)

def apply(obj,properties,skip=()):
    for key,value in properties.items():
        if key not in skip:obj.set_editor_property(key,decode(value))

def create(entry,factory):
    package=entry['path'].split('.')[0]
    folder,name=package.rsplit('/',1)
    obj=unreal.load_asset(package) if EA.does_asset_exist(package) else AT.create_asset(name,folder,getattr(unreal,entry['class']),factory)
    assert obj,package
    return obj

try:
    # Import original raster files in the destination engine; never copy 5.8 packages.
    for entry in S['assets']:
        if entry['class']!='Texture2D':continue
        package=entry['path'].split('.')[0];folder,name=package.rsplit('/',1)
        relative=pathlib.Path(entry['source_file']).relative_to(pathlib.Path(S['source']))
        task=unreal.AssetImportTask()
        task.set_editor_property('filename',str(P/relative))
        task.set_editor_property('destination_path',folder)
        task.set_editor_property('destination_name',name)
        task.set_editor_property('automated',True)
        task.set_editor_property('replace_existing',True)
        task.set_editor_property('save',True)
        AT.import_asset_tasks([task])
        obj=unreal.load_asset(package);assert isinstance(obj,unreal.Texture2D),package
        apply(obj,entry['properties']);EA.save_loaded_asset(obj,False)
        REPORT['assets'].append(package)
    for entry in S['assets']:
        if entry['class'] not in ('PaperSprite','PaperTileSet'):continue
        factory=unreal.PaperSpriteFactory() if entry['class']=='PaperSprite' else unreal.PaperTileSetFactory()
        obj=create(entry,factory)
        apply(obj,entry['properties'])
        EA.save_loaded_asset(obj,False)
        REPORT['assets'].append(entry['path'].split('.')[0])
    world=unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    assert world
    for item in S['actors']:
        cls=item['class']
        actor=AS.spawn_actor_from_class(getattr(unreal,cls),unreal.Vector(0,0,0))
        assert actor,item['label']
        actor.set_actor_label(item['label'])
        actor.set_folder_path(item['folder'])
        actor.set_editor_property('tags',item['tags'])
        component_class={'PaperSpriteActor':unreal.PaperSpriteComponent,'PaperTileMapActor':unreal.PaperTileMapComponent,'PaperGroupedSpriteActor':unreal.PaperGroupedSpriteComponent,'CameraActor':unreal.CameraComponent}[cls]
        c=actor.get_component_by_class(component_class)
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        actor.set_actor_transform(decode(item['transform']),False,False)
        if cls=='PaperSpriteActor':
            assert c.set_sprite(decode(item['sprite']))
        elif cls=='PaperGroupedSpriteActor':
            c.set_editor_property('per_instance_sprite_data',decode(item['instances']))
            assert c.get_instance_count()==len(item['instances'])
        elif cls=='PaperTileMapActor':
            entry=next(e for e in S['assets'] if e['class']=='PaperTileMap')
            pp=entry['properties'];width=pp['map_width'];height=pp['map_height']
            c.create_new_tile_map(width,height,pp['tile_width'],pp['tile_height'],pp['pixels_per_unreal_unit'],False)
            native=c.get_editor_property('tile_map')
            apply(native,pp)
            for z,layer in enumerate(entry['layers']):
                c.add_new_layer()
                for index,value in enumerate(item['cells'][z]):
                    tile=decode(value)
                    if tile.get_editor_property('tile_set') is not None:c.set_tile(index%width,index//width,z,tile)
            for layer,spec in zip(native.get_editor_property('tile_layers'),entry['layers']):apply(layer,spec,('layer_width','layer_height'))
            c.rebuild_collision()
            package=entry['path'].split('.')[0];folder,name=package.rsplit('/',1)
            assert not EA.does_asset_exist(package),'Target tilemap already exists; inspect before retry'
            persistent=AT.duplicate_asset(name,folder,native);assert persistent
            EA.save_loaded_asset(persistent,False)
            c.set_tile_map(persistent)
            REPORT['assets'].append(package)
        apply(c,item['component'],('mobility',))
        if cls!='CameraActor':
            c.set_collision_profile_name(item['collision_profile'])
            c.set_collision_enabled(decode(item['collision_enabled']))
        if 'mobility' in item['component']:c.set_mobility(decode(item['component']['mobility']))
        REPORT['actors'].append(item['label'])
    EA.save_directory('/Game/Reference120m',False,True)
    assert unreal.EditorLoadingAndSavingUtils.save_map(world,'/Game/Levels/L_Reference120m')
    REPORT['success']=True
except Exception:
    REPORT['error']=traceback.format_exc()
    unreal.log_error(REPORT['error'])
finally:
    (P/'Saved/migration57_build.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2),encoding='utf-8')
    unreal.log('UE57_MIGRATION_BUILD '+str(REPORT['success']))
