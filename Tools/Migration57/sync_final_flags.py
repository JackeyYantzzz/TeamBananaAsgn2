import unreal,pathlib,json,runpy
P=pathlib.Path(unreal.Paths.project_dir()).resolve()
assert P.name=='场景地图新版'
flags=json.loads((P/'SourceAssets/UE58Transfer/actor_collision_flags.json').read_text(encoding='utf-8'))
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
assert len(actors)==len(flags)==165
for actor in actors:
    desired=flags[actor.get_actor_label()]
    if actor.get_actor_enable_collision()!=desired:actor.set_actor_enable_collision(desired)
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
runpy.run_path(str(P/'Tools/Migration57/verify_transfer.py'))
