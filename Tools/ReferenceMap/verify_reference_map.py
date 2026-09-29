"""Read-only UE5 audit. Writes only Saved/reference_map_verified.json.

Run with the finished reference level open. No level switching, collision
rebuilding, asset saving, object creation, or native property edits occur.
"""
import datetime
import hashlib
import importlib.util
import json
import math
import pathlib
import traceback

import unreal

LEVEL = '/Game/Levels/L_Reference120m'
ASSET = '/Game/Reference120m/Tiles/TM_Reference120m_LowerStart'
ROOT = '/Game/Reference120m'
REPORT = {
    'audit': 'Final reference Paper2D map, collision and original-source provenance',
    'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'passed': False, 'checks': [], 'failures': [], 'measurements': {},
    'limitations': [
        'Map geometry and editor collision queries only; no character playtest.',
        'Water, spikes, gems and crates are visual placement only.',
        'Jump reachability, damage, swimming and 60-90 second traversal require gameplay integration.',
        'Original-pack artwork approximates the reference composition; it is not identical source artwork.',
    ],
}


def check(name, passed, actual=None):
    result = {'name': name, 'passed': bool(passed)}
    if actual is not None:
        result['actual'] = actual
    REPORT['checks'].append(result)
    if not passed:
        REPORT['failures'].append(result)


def close(a, b, tolerance=.15):
    return math.isclose(float(a), float(b), abs_tol=tolerance, rel_tol=0)


def vec(v):
    return [float(v.x), float(v.y), float(v.z)]


def gid(component, col, row, layer):
    tile = component.get_tile(col, row, layer)
    if tile.get_editor_property('tile_set') is None:
        return 0
    return int(tile.get_editor_property('packed_tile_index')) + 1


def trace(world, start, end):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(*start), unreal.Vector(*end),
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [],
        unreal.DrawDebugTrace.NONE, False)
    if hit is None:
        return False, None, None
    values = hit.to_tuple()
    return bool(values[0]), values[10], values[5]


def load_layout_module():
    name = 'reference_layout_native_audit'
    spec = importlib.util.spec_from_file_location(name, pathlib.Path(__file__).with_name('reference_layout.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit_sources(project):
    copies = project / 'SourceAssets' / 'Reference120m'
    source_root = pathlib.Path('C:/Users/dee04/OneDrive/文档/Unreal Projects/游戏场景最终版/SourceAssets/Reference120m')
    original_records = json.loads((project/'SourceAssets/UE58Transfer/original_source_hashes.json').read_text(encoding='utf-8-sig'))
    hashes = []
    for record in original_records:
        copy_rel = pathlib.Path(record['project_copy']).relative_to(source_root)
        copied = copies / copy_rel
        original_hash = record['source_sha256']
        copied_hash = hashlib.sha256(copied.read_bytes()).hexdigest() if copied.is_file() else None
        hashes.append({'original': record['original'], 'project_copy': str(copied), 'source_sha256': original_hash,
                       'copy_sha256': copied_hash, 'passed': bool(record['passed']) and original_hash == copied_hash})
    REPORT['measurements']['original_source_sha256'] = hashes
    check('All six PNGs match original hashes recorded by the verified UE5.8 project',
          len(hashes) == 6 and all(r['passed'] for r in hashes),
          {'checked':len(hashes), 'failed':[r for r in hashes if not r['passed']]})


def audit():
    project = pathlib.Path(unreal.Paths.project_dir()).resolve()
    check('Correct final project', project.name == '场景地图新版', str(project))
    module = load_layout_module()
    layout = module.make_layout()
    REPORT['measurements']['layout_validation'] = layout['validation']
    audit_sources(project)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = list(subsystem.get_all_level_actors())
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    world_path = world.get_path_name()
    check('Correct reference level currently open', world_path.split('.')[0] == LEVEL, world_path)
    matching = [a for a in actors if a.get_actor_label() == 'TM_Reference120m_EDIT_ME']
    check('Exactly one reference map actor', len(matching) == 1, len(matching))
    if len(matching) != 1:
        return
    actor = matching[0]
    component = actor.get_component_by_class(unreal.PaperTileMapComponent)
    check('Map actor has native PaperTileMapComponent', component is not None)
    if component is None:
        return
    tile_map = component.get_editor_property('tile_map')
    check('Final revised native map asset assigned', tile_map is not None and tile_map.get_path_name().split('.')[0] == ASSET,
          tile_map.get_path_name() if tile_map else None)
    if tile_map is None:
        return
    check('Map is an independently editable saved asset', not component.owns_tile_map())
    for key, expected in [('map_width',240),('map_height',64),('tile_width',64),('tile_height',64)]:
        actual = tile_map.get_editor_property(key)
        check(key, actual == expected, actual)
    check('Pixels per cm is 1.28', close(tile_map.get_editor_property('pixels_per_unreal_unit'),1.28,.00001))
    check('3D map collision enabled', tile_map.get_editor_property('sprite_collision_domain') == unreal.SpriteCollisionMode.USE3D_PHYSICS)
    check('100cm collision thickness', close(tile_map.get_editor_property('collision_thickness'),100))
    check('Unit map world scale', all(close(v,1,.00001) for v in vec(component.get_world_scale())), vec(component.get_world_scale()))
    check('Map actor collision and query enabled', actor.get_actor_enable_collision() and component.is_query_collision_enabled())
    for name, channel in [('Pawn',unreal.CollisionChannel.ECC_PAWN),('Visibility',unreal.CollisionChannel.ECC_VISIBILITY)]:
        response=component.get_collision_response_to_channel(channel)
        check('Map blocks '+name,response==unreal.CollisionResponseType.ECR_BLOCK,str(response))

    layers=list(tile_map.get_editor_property('tile_layers'))
    by_name={str(layer.get_editor_property('layer_name')):(i,layer) for i,layer in enumerate(layers)}
    fields={'Decoration_NoCollision':'decor','SurfaceCollision':'grass','TerrainCollision':'ground','Backdrop_NoCollision':'backdrop_ground'}
    expected_indices={'Decoration_NoCollision':0,'SurfaceCollision':1,'TerrainCollision':2,'Backdrop_NoCollision':3}
    check('Exactly four intended layers',set(by_name)==set(fields),list(by_name))
    if not set(fields).issubset(by_name):
        return
    for name,(index,layer) in by_name.items():
        check(name+' order',index==expected_indices[name],index)
        check(name+' collision',bool(layer.get_editor_property('layer_collides'))==(name in layout['collision_layer_names']),bool(layer.get_editor_property('layer_collides')))
        check(name+' size',layer.get_editor_property('layer_width')==240 and layer.get_editor_property('layer_height')==64)

    left=component.get_tile_corner_position(0,64,by_name['TerrainCollision'][0],True)
    right=component.get_tile_corner_position(240,64,by_name['TerrainCollision'][0],True)
    REPORT['measurements']['map_corners']={'left_bottom':vec(left),'right_bottom':vec(right)}
    check('Map origin and exact 12000cm span',close(left.x,0) and close(left.z,0) and close(right.x,12000) and close(right.z,0),REPORT['measurements']['map_corners'])
    mismatch_count=0; examples=[]; counts={name:0 for name in fields}
    for name,key in fields.items():
        index=by_name[name][0]
        for offset,expected in enumerate(layout[key]):
            col,row=offset%240,offset//240
            actual=gid(component,col,row,index)
            counts[name]+=int(actual!=0)
            if actual!=expected:
                mismatch_count+=1
                if len(examples)<24:examples.append({'layer':name,'column':col,'row':row,'expected':expected,'actual':actual})
    REPORT['measurements']['native_tile_counts']=counts
    check('All 61440 native cells match the traced layout',mismatch_count==0,
          {'cells_checked':240*64*4,'mismatch_count':mismatch_count,'first_mismatches':examples})

    spike_results=[]
    for hazard in layout['spikes']:
        row=hazard['ground_row']
        ok=all(gid(component,col,row,by_name['SurfaceCollision'][0])==module.GRASS and
               gid(component,col,row-1,by_name['Decoration_NoCollision'][0])==module.SPIKE
               for col in range(hazard['column_start'],hazard['column_end']))
        spike_results.append({'id':hazard['id'],'passed':ok,'ground_row':row})
    check('All six spike groups rest on grass',len(spike_results)==6 and all(r['passed'] for r in spike_results),spike_results)
    check('All 24 reference stepping platforms are present',len(layout['floating_platforms'])==24 and all(
        gid(component,col,p['row'],by_name['SurfaceCollision'][0])==module.THIN
        for p in layout['floating_platforms'] for col in range(p['column_start'],p['column_end'])),len(layout['floating_platforms']))

    def top_trace(col,row,kind):
        x,z=(col+.5)*50,(64-row)*50
        blocking,hit_component,point=trace(world,(x,0,z+8),(x,0,z-8))
        return {'kind':kind,'column':col,'row':row,'expected_z':z,
                'passed':blocking and hit_component==component and point is not None and close(point.z,z),
                'blocking':blocking,'impact':vec(point) if point is not None else None,
                'hit_component':hit_component.get_path_name() if hit_component else None}

    # Test every exposed top of the union of the two collision layers. This
    # excludes tiles buried inside solid terrain and ignores visual soil.
    top_results=[]
    for row in range(64):
        for col in range(240):
            n=row*240+col
            occupied=bool(layout['ground'][n] or layout['grass'][n])
            above=bool(row and (layout['ground'][n-240] or layout['grass'][n-240]))
            if occupied and not above:
                top_results.append(top_trace(col,row,'surface' if layout['grass'][n] else 'terrain'))
    REPORT['measurements']['exposed_top_trace_counts']={key:sum(r['kind']==key for r in top_results) for key in ('surface','terrain')}
    check('All exposed terrain and cap tops block at intended height',bool(top_results) and all(r['passed'] for r in top_results),
          {'checked':len(top_results),'failed':[r for r in top_results if not r['passed']]})
    platform_results=[]
    for p in layout['floating_platforms']:
        col=(p['column_start']+p['column_end']-1)//2
        result=top_trace(col,p['row'],p['id'])
        platform_results.append(result)
    REPORT['measurements']['platform_collision_traces']=platform_results
    check('Every one of 24 small platforms has physical top collision',len(platform_results)==24 and all(r['passed'] for r in platform_results),
          {'checked':len(platform_results),'failed':[r for r in platform_results if not r['passed']]})

    # Pick clear interior points in rear-only soil and trace across the plane.
    rear_results=[]
    for row in range(2,62):
        for col in range(2,238):
            n=row*240+col
            if not layout['backdrop_ground'][n] or layout['ground'][n] or layout['grass'][n]:continue
            if len(rear_results)>=16:break
            if col%7 or row%5:continue
            x,z=(col+.5)*50,(64-row-.5)*50
            blocking,hit_component,point=trace(world,(x,-200,z),(x,200,z))
            rear_results.append({'column':col,'row':row,'passed':not blocking,'unexpected_component':hit_component.get_path_name() if hit_component else None})
        if len(rear_results)>=16:break
    check('Rear terrain is passable at sampled interior positions',bool(rear_results) and all(r['passed'] for r in rear_results),rear_results)

    sprite_actors=[a for a in actors if isinstance(a,unreal.PaperSpriteActor)]
    sprite_results=[]
    for visual in sprite_actors:
        c=visual.get_component_by_class(unreal.PaperSpriteComponent)
        sprite=c.get_sprite() if c else None
        texture=sprite.get_editor_property('source_texture') if sprite else None
        valid=bool(sprite and texture and sprite.get_path_name().startswith(ROOT+'/'))
        sprite_results.append({'actor':visual.get_actor_label(),'passed':valid,'sprite':sprite.get_path_name() if sprite else None,
                               'source_texture':texture.get_path_name() if texture else None,
                               'collision':bool(visual.get_actor_enable_collision() and c and c.is_collision_enabled())})
    check('138 native sprite actors have valid assigned original-pack sprites',len(sprite_results)==138 and all(r['passed'] for r in sprite_results),
          {'count':len(sprite_results),'failed':[r for r in sprite_results if not r['passed']]})
    check('Scenery sprite actors do not collide',all(not r['collision'] for r in sprite_results),
          [r for r in sprite_results if r['collision']])
    REPORT['measurements']['sprite_actor_bindings']=sprite_results
    water_results=[]
    for rect in layout['water_rects']:
        matches=[a for a in actors if a.get_actor_label()==rect['name']]
        water_actor=matches[0] if len(matches)==1 else None
        comp=water_actor.get_component_by_class(unreal.PaperGroupedSpriteComponent) if water_actor else None
        count=comp.get_instance_count() if comp else 0
        no_collision=bool(water_actor and comp and not water_actor.get_actor_enable_collision() and not comp.is_collision_enabled())
        location=water_actor.get_actor_location() if water_actor else None
        placed=bool(location and close(location.x,rect['x']) and close(location.z,rect['bottomZ']))
        water_results.append({'actor':rect['name'],'type':rect['type'],'instances':count,'passed':len(matches)==1 and count>0 and no_collision and placed,'no_collision':no_collision,'location':vec(location) if location else None})
    REPORT['measurements']['water_actors']=water_results
    check('Two water basins and five waterfalls exist without collision',len(water_results)==7 and
          sum(r['type']=='basin' for r in water_results)==2 and sum(r['type']=='waterfall' for r in water_results)==5 and all(r['passed'] for r in water_results),water_results)

    sky=[a for a in sprite_actors if a.get_actor_label()=='BG_000_sky']
    if len(sky)==1:
        c=sky[0].get_component_by_class(unreal.PaperSpriteComponent)
        s=c.get_sprite();dimensions=s.get_editor_property('source_dimension');scale=sky[0].get_actor_scale3d();p=sky[0].get_actor_location()
        width=abs(dimensions.x*scale.x);height=abs(dimensions.y*scale.z)
        bounds={'min_x':p.x-width/2,'max_x':p.x+width/2,'min_z':p.z-height/2,'max_z':p.z+height/2}
        check('Blue sky covers the full reference frame and edges',bounds['min_x']<=0 and bounds['max_x']>=12000 and bounds['min_z']<=(510-683)*12000/2048 and bounds['max_z']>=510*12000/2048,bounds)
    else:
        check('Blue sky backing exists exactly once',False,len(sky))


try:
    audit()
except Exception:
    error=traceback.format_exc()
    REPORT['failures'].append({'name':'Audit execution','passed':False,'error':error})
    unreal.log_error(error)
finally:
    REPORT['passed']=not REPORT['failures']
    REPORT['check_count']=len(REPORT['checks'])
    path=pathlib.Path(unreal.Paths.project_dir())/'Saved'/'reference_map_verified.json'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(REPORT,ensure_ascii=False,indent=2),encoding='utf-8')
    unreal.log('REFERENCE_MAP_VERIFIED {}: {}'.format('PASS' if REPORT['passed'] else 'FAIL',path))
