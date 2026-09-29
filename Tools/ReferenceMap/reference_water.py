"""Reference pools and falls built from the user's original platform atlas.

No raster file is created or modified. The water uses the pack's two existing
water tiles and a white patch inside its existing blue saw for foam. All actors
are visual only and have no collision. This module has no import-time effects.

Public API: build_water(actor_subsystem, asset_root, texture, rectangles)
Rectangles use world centimetres: x,z are LOWER LEFT, width,height are positive;
kind is 'pool' or 'waterfall'. Explicit anchor='center' also accepts centres.
Optional depth_y overrides the default 4 cm, in front of the terrain plane.
reference_layout.make_layout()['water_rects'] works directly too: bottomZ is
mapped to z and type='basin' is mapped to kind='pool'.
"""

import math

SOURCE_PACK = 'Simplified Platformer Pack'
SOURCE_REGIONS = {
    'body': ((256, 64), (64, 64), '18'),
    'crest': ((256, 0), (64, 12), '4'),
    'foam': ((668, 28), (8, 8), '10_white_interior'),
}


def normalise_rectangle(rect):
    """Validate and normalise dimensions without loading Unreal."""
    data = dict(rect)
    if 'z' not in data and 'bottomZ' in data:
        data['z'] = data['bottomZ']
    for key in ('x', 'z', 'width', 'height'):
        data[key] = float(data[key])
        if not math.isfinite(data[key]):
            raise ValueError('Water rectangle contains a non-finite ' + key)
    if data['width'] <= 0 or data['height'] <= 0:
        raise ValueError('Water rectangle must have positive width and height')
    data['kind'] = str(data.get('kind', data.get('type', 'pool'))).lower()
    if data['kind'] == 'basin':
        data['kind'] = 'pool'
    if data['kind'] not in ('pool', 'waterfall'):
        raise ValueError('Unknown water kind: ' + data['kind'])
    anchor = data.get('anchor', 'lower_left')
    if anchor == 'center':
        data['x'] -= data['width'] / 2
        data['z'] -= data['height'] / 2
    elif anchor not in ('lower_left', 'bottom_left'):
        raise ValueError('Water anchor must be lower_left, bottom_left or center')
    data['depth_y'] = float(data.get('depth_y', 4.0))
    data['anchor'] = 'lower_left'
    return data


def create_water_sprites(asset_root, texture):
    import unreal
    if isinstance(texture, str):
        texture = unreal.load_asset(texture)
    if not isinstance(texture, unreal.Texture2D):
        raise TypeError('Water source must be the original imported Texture2D')
    folder = asset_root.rstrip('/') + '/Water/Sprites'
    unreal.EditorAssetLibrary.make_directory(folder)
    material = unreal.load_asset('/Paper2D/MaskedUnlitSpriteMaterial')
    sprites = {}
    for key, (uv, dimensions, tile_id) in SOURCE_REGIONS.items():
        name = 'S_ReferenceWater_' + key.title()
        sprite = unreal.load_asset(folder + '/' + name)
        if sprite is None:
            sprite = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
                name, folder, unreal.PaperSprite, unreal.PaperSpriteFactory())
        if sprite is None:
            raise RuntimeError('Could not create water sprite: ' + name)
        sprite.set_editor_property('source_texture', texture)
        sprite.set_editor_property('source_uv', unreal.Vector2D(*uv))
        sprite.set_editor_property('source_dimension', unreal.Vector2D(*dimensions))
        sprite.set_editor_property('pivot_mode', unreal.SpritePivotMode.CENTER_CENTER)
        sprite.set_editor_property('pixels_per_unreal_unit', 1.0)
        sprite.set_editor_property('sprite_collision_domain', unreal.SpriteCollisionMode.NONE)
        sprite.set_editor_property('default_material', material)
        geometry = sprite.get_editor_property('render_geometry')
        geometry.set_editor_property('geometry_type', unreal.SpritePolygonMode.SOURCE_BOUNDING_BOX)
        sprite.set_editor_property('render_geometry', geometry)
        unreal.EditorAssetLibrary.set_metadata_tag(sprite, 'SourcePack', SOURCE_PACK)
        unreal.EditorAssetLibrary.set_metadata_tag(sprite, 'SourceTileIndex', tile_id)
        unreal.EditorAssetLibrary.set_metadata_tag(sprite, 'Purpose', 'WaterVisualOnly_NoGameplay')
        unreal.EditorAssetLibrary.save_loaded_asset(sprite, False)
        sprites[key] = sprite
    return sprites


def build_water(actor_subsystem, asset_root, texture, rectangles):
    """Build native grouped sprites. Return actors, serialisable report, sprites."""
    import unreal
    rects = [normalise_rectangle(rect) for rect in rectangles]
    sprites = create_water_sprites(asset_root, texture)
    created = []
    report = []
    for number, rect in enumerate(rects, 1):
        left, bottom, width, height = [rect[k] for k in ('x', 'z', 'width', 'height')]
        kind = rect['kind']
        actor = actor_subsystem.spawn_actor_from_class(
            unreal.PaperGroupedSpriteActor,
            unreal.Vector(left, rect['depth_y'], bottom),
            unreal.Rotator(pitch=0, yaw=0, roll=0))
        label = rect.get('name') or ('Water_%s_%02d' % (kind.title(), number))
        actor.set_actor_label(label)
        actor.set_folder_path('ReferenceMap/Water')
        actor.set_actor_enable_collision(False)
        actor.set_editor_property('tags', ['WaterVisualOnly', 'OriginalPackWaterTiles4And18',
            'NoSwimmingOrDamageLogic', 'ReferenceKind=' + kind])
        comp = actor.get_component_by_class(unreal.PaperGroupedSpriteComponent)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        comp.set_editor_property('cast_shadow', False)

        def piece(key, x, z, w, h, y=0.0, color=(1, 1, 1, 1), rotate=False):
            source_w, source_h = SOURCE_REGIONS[key][1]
            # Positive pitch rotates within Paper2D's X/Z plane. Exchange the
            # scale axes for the 90 degree waterfall wave orientation.
            scale = (h / source_w, 1, w / source_h) if rotate else (w / source_w, 1, h / source_h)
            transform = unreal.Transform(
                location=unreal.Vector(x, y, z),
                rotation=unreal.Rotator(pitch=90 if rotate else 0, yaw=0, roll=0),
                scale=unreal.Vector(*scale))
            comp.add_instance(transform, sprites[key], False, unreal.LinearColor(*color))

        # The body samples water tile 18. Its native wave pattern remains
        # visible; a vertex tint provides the reference's saturated blue water.
        cell = 93.75
        columns = max(1, int(math.ceil(width / cell)))
        rows = max(1, int(math.ceil(height / cell)))
        body_tint = (0.025, 0.55, 0.97, 1.0)
        if kind == 'waterfall':
            body_tint = (0.18, 0.82, 1.0, 1.0)
        for row in range(rows):
            h = min(cell, height - row * cell)
            for column in range(columns):
                w = min(cell, width - column * cell)
                piece('body', column * cell + w / 2, row * cell + h / 2,
                      w, h, color=body_tint, rotate=kind == 'waterfall')

        if kind == 'waterfall':
            # Narrow white/cyan vertical trails echo the reference waterfall.
            # These pieces also come from the original atlas (white saw centre).
            count = max(3, int(width / 18.0))
            for i in range(count):
                x = (i + 0.5) * width / count
                streak_height = height * (0.68 + 0.20 * ((i * 7) % 5) / 4.0)
                offset = height * (0.03 + 0.09 * ((i * 3) % 4) / 3.0)
                piece('foam', x, height - offset - streak_height / 2,
                      2.0 + (i % 3), streak_height, 0.5,
                      (0.48, 0.9, 1.0, 1.0) if i % 2 else (0.92, 1.0, 1.0, 1.0))
            for edge in (2.0, width - 2.0):
                piece('foam', edge, height / 2, 2.5, height * 0.98, 0.6,
                      (0.8, 1.0, 1.0, 1.0))
            # Rounded-looking foam scallops use the existing wave crest.
            for i in range(columns):
                w = min(cell, width - i * cell)
                piece('crest', i * cell + w / 2, 5.0, w, 20, 0.8)
        else:
            # Small highlights are atlas samples too. Deterministic placement
            # keeps a rebuild visually identical without random global state.
            flecks = min(90, max(8, int(width * height / 10000.0)))
            for i in range(flecks):
                x = width * (((i * 0.61803398875) + 0.21) % 1)
                z = height * (0.08 + 0.80 * (((i * 0.41421356237) + 0.17) % 1))
                piece('foam', x, z, 3.2 + (i % 2), 3.2, 0.4,
                      (0.22, 0.75, 1.0, 1.0))

        # Shared original wavy crest at the upper water line.
        for i in range(columns):
            w = min(cell, width - i * cell)
            piece('crest', i * cell + w / 2, height - 7.0, w, 18.0, 1.0)
        created.append(actor)
        report.append(dict(rect, actor=label, sprite_instances=comp.get_instance_count(),
                           collision=False, gameplay=False,
                           source_regions=SOURCE_REGIONS))
    return {'actors': created, 'report': report, 'sprites': sprites}
