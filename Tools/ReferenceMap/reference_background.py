"""Native Paper2D scenery assembled from the user's Background Elements Redux.

No image is generated, recoloured on disk, or replaced. Sprite UVs sample the
original PNGs; native vertex tints and transforms arrange the reference's blue
sky, cloud banks, layered green meadow and trees. This module has no import-time
side effects and can be imported outside Unreal for placement validation.

Public editor API:
    result = build_background(actors, asset_root, source_dir)
    sprites = result['sprites']
    add_sprite(actors, sprites['tree'], x, z, width, height, y=-15,
               label='Tree_Foreground_01', folder='ReferenceMap/Foliage')

All add_sprite coordinates are centre coordinates in world centimetres.
"""

from pathlib import Path

PACK_NAME = 'Background Elements Redux'
SCALE = 12000.0 / 2048.0
BASELINE = 510.0

# Native sprite atlas regions from the pack's own spritesheet_default.xml.
ATLAS_REGIONS = {
    'tree': ((853, 233), (94, 204)),
    'treeLong': ((947, 0), (82, 249)),
    'treeSmall1': ((103, 1051), (20, 43)),
    'treeSmall2': ((597, 65), (23, 68)),
    'treeSmall3': ((971, 1031), (30, 49)),
    'bush1': ((419, 950), (120, 60)),
    'bush2': ((0, 1051), (53, 44)),
    'bush3': ((725, 511), (59, 52)),
    'bush4': ((871, 1034), (50, 46)),
    'bushAlt1': ((0, 1004), (141, 47)),
    'bushOrange1': ((281, 156), (124, 59)),
    'cloud1': ((250, 365), (203, 121)),
    'cloud2': ((281, 0), (196, 156)),
    'cloud3': ((0, 865), (216, 139)),
    'cloud4': ((0, 363), (250, 146)),
}

SOURCES = {
    'Atlas': 'Spritesheet/spritesheet_default.png',
    'Sky': 'Backgrounds/backgroundEmpty.png',
    'CloudBank': 'Backgrounds/Elements/cloudLayer1.png',
    'Meadow': 'Backgrounds/Elements/groundLayer1.png',
    'Hills': 'Backgrounds/Elements/hills.png',
}


def source_manifest(source_dir):
    root = Path(source_dir)
    return {key: str(root / relative) for key, relative in SOURCES.items()}


def _import_texture(asset_root, key, filename):
    import unreal
    name = 'T_BG_' + key
    path = asset_root + '/Textures/' + name
    texture = unreal.load_asset(path)
    if texture is None:
        task = unreal.AssetImportTask()
        task.set_editor_property('filename', str(filename))
        task.set_editor_property('destination_path', asset_root + '/Textures')
        task.set_editor_property('destination_name', name)
        task.set_editor_property('automated', True)
        task.set_editor_property('replace_existing', False)
        task.set_editor_property('save', True)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        texture = unreal.load_asset(path)
    if not isinstance(texture, unreal.Texture2D):
        raise RuntimeError('Failed to import original background texture: ' + str(filename))
    texture.set_editor_property('filter', unreal.TextureFilter.TF_NEAREST)
    texture.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    texture.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_PIXELS2D)
    unreal.EditorAssetLibrary.set_metadata_tag(texture, 'SourcePack', PACK_NAME)
    unreal.EditorAssetLibrary.set_metadata_tag(texture, 'OriginalSourceFile', str(filename))
    unreal.EditorAssetLibrary.save_loaded_asset(texture, False)
    return texture


def import_sprite(asset_root, key, texture, uv, dimensions):
    """Make/update a native collision-free sprite from an original texture UV."""
    import unreal
    name = 'S_BG_' + key
    folder = asset_root + '/Sprites'
    path = folder + '/' + name
    sprite = unreal.load_asset(path)
    if sprite is None:
        sprite = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, folder, unreal.PaperSprite, unreal.PaperSpriteFactory())
    if sprite is None:
        raise RuntimeError('Could not create original-pack sprite: ' + path)
    sprite.set_editor_property('source_texture', texture)
    sprite.set_editor_property('source_uv', unreal.Vector2D(*uv))
    sprite.set_editor_property('source_dimension', unreal.Vector2D(*dimensions))
    sprite.set_editor_property('pivot_mode', unreal.SpritePivotMode.CENTER_CENTER)
    sprite.set_editor_property('pixels_per_unreal_unit', 1.0)
    sprite.set_editor_property('sprite_collision_domain', unreal.SpriteCollisionMode.NONE)
    sprite.set_editor_property('default_material',
                               unreal.load_asset('/Paper2D/MaskedUnlitSpriteMaterial'))
    geometry = sprite.get_editor_property('render_geometry')
    geometry.set_editor_property('geometry_type', unreal.SpritePolygonMode.SOURCE_BOUNDING_BOX)
    sprite.set_editor_property('render_geometry', geometry)
    unreal.EditorAssetLibrary.set_metadata_tag(sprite, 'SourcePack', PACK_NAME)
    unreal.EditorAssetLibrary.set_metadata_tag(sprite, 'OriginalUV', '%s;%s' % (uv, dimensions))
    unreal.EditorAssetLibrary.save_loaded_asset(sprite, False)
    return sprite


def create_sprite_assets(asset_root, source_dir):
    """Import five byte-original PNGs, return reusable background/foliage sprites."""
    import unreal
    root = asset_root.rstrip('/') + '/Background'
    unreal.EditorAssetLibrary.make_directory(root + '/Textures')
    unreal.EditorAssetLibrary.make_directory(root + '/Sprites')
    files = source_manifest(source_dir)
    missing = [filename for filename in files.values() if not Path(filename).is_file()]
    if missing:
        raise FileNotFoundError('Original pack files missing: ' + ', '.join(missing))
    textures = {key: _import_texture(root, key, filename) for key, filename in files.items()}
    sprites = {key: import_sprite(root, key, textures['Atlas'], uv, dimensions)
               for key, (uv, dimensions) in ATLAS_REGIONS.items()}
    # An existing uniform sky patch supplies the full scene backing. Changing
    # native vertex colour leaves the user's source texture byte-identical.
    sprites['sky'] = import_sprite(root, 'Sky', textures['Sky'], (32, 32), (8, 8))
    sprites['cloudBank'] = import_sprite(root, 'CloudBank', textures['CloudBank'], (0, 0), (1024, 400))
    sprites['meadow'] = import_sprite(root, 'Meadow', textures['Meadow'], (0, 0), (1024, 400))
    sprites['hills'] = import_sprite(root, 'Hills', textures['Hills'], (0, 0), (1024, 400))
    return sprites


def add_sprite(actors, sprite, x, z, width, height, y=-300,
               tint=(1, 1, 1, 1), label='Background_Element',
               folder='ReferenceMap/Background', mirrored=False):
    """Spawn one editable native PaperSpriteActor; centre-based centimetres."""
    import unreal
    if width <= 0 or height <= 0:
        raise ValueError('Sprite dimensions must be positive')
    actor = actors.spawn_actor_from_class(
        unreal.PaperSpriteActor, unreal.Vector(float(x), float(y), float(z)),
        unreal.Rotator(pitch=0, yaw=0, roll=0))
    actor.set_actor_label(label)
    actor.set_folder_path(folder)
    actor.set_actor_enable_collision(False)
    actor.set_editor_property('tags', ['OriginalPackBackground', 'VisualOnly'])
    component = actor.get_component_by_class(unreal.PaperSpriteComponent)
    # PaperSpriteActor's native constructor defaults to STATIC. Its runtime
    # setters silently reject sprite/colour changes on a registered static
    # component, so temporarily enable those changes during editor assembly.
    component.set_mobility(unreal.ComponentMobility.MOVABLE)
    component.set_sprite(sprite)
    if component.get_sprite() != sprite:
        raise RuntimeError('PaperSprite assignment was rejected: ' + label)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property('cast_shadow', False)
    component.set_sprite_color(unreal.LinearColor(*tint))
    dimensions = sprite.get_editor_property('source_dimension')
    actor.set_actor_scale3d(unreal.Vector(
        width / dimensions.x * (-1 if mirrored else 1), 1, height / dimensions.y))
    component.set_mobility(unreal.ComponentMobility.STATIC)
    return actor


def _placement(key, left, top, width, height, depth, tint=(1, 1, 1, 1), mirror=False):
    return dict(sprite=key, x=(left + width / 2) * SCALE,
                z=(BASELINE - top - height / 2) * SCALE,
                width=width * SCALE, height=height * SCALE,
                y=depth, tint=tint, mirrored=mirror)


def reference_placements():
    """Deterministic original-art placements matching the reference composition."""
    result = []
    # Large blue backing covers all of the wide overview and camera edge margin.
    result.append(dict(sprite='sky', x=6000, z=1100, width=14000,
                       height=5600, y=-1000, tint=(0.001, 0.25, 0.70, 1), mirrored=False))
    # Continuous distant white bank beneath separate tall, puffy cloud groups.
    for index in range(4):
        result.append(_placement('cloudBank', index * 512, 258 + (index % 2) * 9,
                                 512, 252 - (index % 2) * 9, -850,
                                 (0.87, 0.97, 1, 1), bool(index % 2)))
    clouds = [
        ('cloud2', 79, 172, 100, 166),
        ('cloud1', 179, 245, 167, 128),
        ('cloud3', 310, 276, 146, 102),
        ('cloud2', 527, 173, 186, 199),
        ('cloud4', 662, 216, 148, 151),
        ('cloud2', 757, 203, 119, 156),
        ('cloud3', 1111, 188, 136, 166),
        ('cloud2', 1270, 180, 163, 177),
        ('cloud4', 1568, 247, 157, 131),
        ('cloud2', 1651, 216, 130, 156),
        ('cloud1', 1860, 277, 152, 116),
        ('cloud2', 1945, 186, 121, 188),
    ]
    for index, (key, left, top, width, height) in enumerate(clouds):
        result.append(_placement(key, left, top, width, height, -780 + index * 0.1))
    # Three overlapping, fully filled green bands reproduce the open meadow.
    # Their bottom is exactly the reference's baseline, leaving blue below it.
    layers = [
        ('hills', 318, -640, (0.27, 0.73, 0.35, 1)),
        ('meadow', 327, -510, (0.18, 0.58, 0.24, 1)),
        ('meadow', 346, -290, (0.13, 0.46, 0.17, 1)),
    ]
    for key, top, depth, tint in layers:
        for index in range(4):
            result.append(_placement(key, index * 512, top, 512, BASELINE - top,
                                     depth, tint, bool(index % 2)))
    # Different tree heights/depths create the reference's repeated forest
    # skyline without stretching one low-resolution forest image across 120 m.
    far = [
        (86, 323, 44), (173, 333, 38), (247, 345, 50),
        (324, 352, 42), (401, 335, 51), (463, 323, 76),
        (539, 346, 44), (631, 338, 54), (693, 345, 38),
        (750, 334, 52), (812, 340, 42), (881, 327, 70),
        (937, 339, 43), (1035, 333, 55), (1100, 340, 70),
        (1176, 330, 62), (1273, 338, 60), (1352, 342, 52),
        (1433, 352, 43), (1490, 341, 50), (1560, 346, 48),
        (1660, 345, 44), (1753, 350, 42), (1821, 342, 53),
        (1880, 337, 70), (1954, 345, 56), (2016, 342, 56),
    ]
    for index, (x, bottom, height) in enumerate(far):
        # Retain natural tree proportions. Their bases sit just behind the
        # nearer meadow silhouette instead of stretching the trunks downward.
        draw_bottom = 348 + (index % 3) * 3
        top = draw_bottom - height
        result.append(_placement('treeLong' if index % 3 else 'tree',
                                 x - height * 0.18, top,
                                 height * 0.36, height, -580 + index * 0.01,
                                 (0.35, 0.85, 0.86, 1), bool(index % 2)))
    middle = [
        (121, 378, 66), (358, 388, 60), (429, 363, 97),
        (500, 346, 130), (781, 389, 68), (900, 351, 108),
        (1170, 382, 70), (1384, 396, 69), (1494, 398, 71),
        (1793, 416, 78), (1919, 400, 99), (2015, 383, 91),
    ]
    for index, (x, bottom, height) in enumerate(middle):
        draw_height = height * 0.72
        draw_width = draw_height * 0.41
        draw_bottom = 375 + (index % 3) * 3
        top = draw_bottom - draw_height
        result.append(_placement('tree' if index % 3 else 'treeLong',
                                 x - draw_width / 2, top,
                                 draw_width, draw_height, -390 + index * 0.01,
                                 (0.43, 0.84, 0.59, 1), bool(index % 2)))
    return result


def build_background(actors, asset_root, source_dir):
    """Build scenery; return reusable sprite dictionary and serializable stats."""
    sprites = create_sprite_assets(asset_root, source_dir)
    placements = reference_placements()
    spawned = []
    for index, data in enumerate(placements):
        values = dict(data)
        key = values.pop('sprite')
        spawned.append(add_sprite(actors, sprites[key], **values,
            label='BG_%03d_%s' % (index, key), folder='ReferenceMap/Background'))
    stats = dict(actor_count=len(spawned), original_pack=PACK_NAME,
                 source_texture_count=len(SOURCES), sprite_count=len(sprites),
                 map_width_cm=12000, background_bounds_cm=[-1000, 13000, -1700, 3900],
                 cloud_groups=12, cloud_banks=4, tree_count=39, meadow_layers=3,
                 source_files=source_manifest(source_dir),
                 generated_or_edited_raster_images=False, collision=False)
    return {'sprites': sprites, 'actors': spawned, 'stats': stats}
