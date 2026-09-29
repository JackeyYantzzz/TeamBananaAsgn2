"""Hand traced layout for the user's final UE5 reference map.

This module only describes a map. It neither edits images nor imports Unreal.
All drawing coordinates use the displayed 2048 x 683 reference canvas.
The original atlas remains the sole source of tile pixels.
"""
from __future__ import annotations

import json
from pathlib import Path

WIDTH, HEIGHT, TILE_SIZE = 240, 64, 64
CELL_SIZE, PPU, ORIGIN_ROW = 50.0, 1.28, 64
SPAN_CM = 12000.0
REFERENCE_WIDTH, REFERENCE_HEIGHT, REFERENCE_BASE_Y = 2048, 683, 510
SCALE = SPAN_CM / REFERENCE_WIDTH
EMPTY, GRASS, SOIL, THIN, SPIKE, GEM, PLANT, CRATE = 0, 1, 4, 29, 71, 51, 73, 75
WATER_SURFACE, WATER_FILL = 5, 19


def world(x, y):
    """Reference pixels -> (world X, world Z), in centimetres."""
    return round(x * SCALE, 4), round((REFERENCE_BASE_Y - y) * SCALE, 4)


def cell(x, y):
    wx, wz = world(x, y)
    return round(wx / CELL_SIZE), round(ORIGIN_ROW - wz / CELL_SIZE)


def cell_world(column, row):
    return (column + 0.5) * CELL_SIZE, (ORIGIN_ROW - row) * CELL_SIZE


def _inside(x, y, points):
    hit = False
    j = len(points) - 1
    for i, (xi, yi) in enumerate(points):
        xj, yj = points[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            hit = not hit
        j = i
    return hit


def _stamp_polygon(grid, points, gid=SOIL):
    for row in range(HEIGHT):
        py = REFERENCE_BASE_Y - (ORIGIN_ROW - row - 0.5) * CELL_SIZE / SCALE
        for column in range(WIDTH):
            px = (column + 0.5) * CELL_SIZE / SCALE
            if _inside(px, py, points):
                grid[row * WIDTH + column] = gid


def _stamp_surface(grid, x1, x2, y, gid=GRASS):
    c1, row = cell(x1, y)
    c2, _ = cell(x2, y)
    if 0 <= row < HEIGHT:
        for column in range(max(0, c1), min(WIDTH, max(c1 + 1, c2))):
            grid[row * WIDTH + column] = gid
    return c1, c2, row


def _object(kind, x, y, **extra):
    wx, wz = world(x, y)
    return {"kind": kind, "x": wx, "baseZ": wz, "image_x": x, "image_y": y, **extra}


def make_layout():
    n = WIDTH * HEIGHT
    ground, backdrop, grass, decor, water = ([0] * n for _ in range(5))
    # Rear terraces have visible soil but no body collision. The caps remain
    # standable, and the small steps in front of the cliffs stay usable.
    polygons = [
        {"name": "Left_high_cliff", "role": "backdrop", "points": [(0,174),(33,174),(33,194),(92,194),(92,510),(0,510)]},
        {"name": "Left_rear_terraces", "role": "backdrop", "points": [(92,298),(141,298),(141,319),(261,319),(261,350),(339,350),(339,405),(365,405),(365,359),(440,359),(440,394),(461,394),(461,510),(82,510),(82,433.2),(92,433.2)]},
        {"name": "Left_low_shelf", "role": "foreground", "points": [(17,447),(82,447),(82,510),(17,510)]},
        # Opening path: 350cm shelf -> 450cm lip -> 550cm deck -> 600cm terrain.
        {"name": "Left_front_terraces", "role": "foreground", "points": [(82,433.2),(139,433.2),(139,416.1333333333),(287,416.1333333333),(287,404),(366,404),(366,440),(419,440),(419,394),(461,394),(461,510),(82,510)]},
        {"name": "First_water_island", "role": "foreground", "points": [(563,351),(621,351),(621,510),(563,510)]},
        {"name": "Middle_rear_terraces", "role": "backdrop", "points": [(659,380),(692,380),(692,311),(778,311),(778,360),(924,360),(924,287),(965,287),(965,203),(1071,203),(1071,252),(1128,252),(1128,335),(1071,335),(1071,510),(659,510)]},
        {"name": "Middle_low_west_shelf", "role": "foreground", "points": [(659,380),(718,380),(718,418),(703,418),(703,510),(659,510)]},
        {"name": "Middle_front_terraces", "role": "foreground", "points": [(703,418),(817,418),(817,434),(966,434),(966,510),(703,510)]},
        {"name": "Central_tower_base", "role": "foreground", "points": [(966,495),(1071,495),(1071,510),(966,510)]},
        {"name": "Waterfall_low_shelf", "role": "foreground", "points": [(1071,440),(1181,440),(1181,510),(1071,510)]},
        {"name": "Bridge_roof", "role": "backdrop", "points": [(1155,305),(1196,305),(1196,270),(1384,270),(1384,286),(1417,286),(1417,321),(1399,321),(1399,335),(1303,335),(1303,360),(1173,360),(1173,440),(1155,440)]},
        {"name": "Under_bridge_floating_corridor", "role": "foreground", "points": [(1173,364),(1303,364),(1303,396),(1369,396),(1369,444),(1224,444),(1224,467),(1181,467),(1181,440),(1173,440)]},
        {"name": "East_water_pillar", "role": "foreground", "points": [(1417,326),(1480,326),(1480,399),(1465,399),(1465,510),(1417,510)]},
        {"name": "Final_rear_terraces", "role": "backdrop", "points": [(1581,319),(1720,319),(1720,341),(1797,341),(1797,409),(1773,409),(1773,439),(2048,439),(2048,510),(1601,510),(1601,359),(1581,359)]},
        {"name": "Final_front_terraces", "role": "foreground", "points": [(1624,411),(1773,411),(1773,439),(2048,439),(2048,510),(1624,510)]},
    ]
    surfaces = []
    for poly in polygons:
        grid = backdrop if poly["role"] == "backdrop" else ground
        _stamp_polygon(grid, poly["points"])
        # Clockwise polygon top contours run to the right. Bottom contours
        # run left; excluding them avoids upside-down grass beneath ceilings.
        points = poly["points"]
        for i, (x1, y1) in enumerate(points):
            x2, y2 = points[(i + 1) % len(points)]
            if y1 == y2 and x2 > x1 and y1 < 490:
                c1, c2, row = _stamp_surface(grass, x1, x2, y1)
                surfaces.append({"name": poly["name"], "image": [x1,x2,y1], "column_start":c1, "column_end":c2, "row":row, "role":poly["role"]})

    # Specific hand traced stepping stones, including the central climb and
    # the descending platforms over the eastern basin.
    platform_specs = [
        (36,49,242),(70,83,249),(50,64,299),(40,54,348),(65,79,358),(58,72,376),
        (176,233,286),
        (488,513,384),(510,541,374),(503,534,408),
        (991,1008,227),(1033,1048,273),(1008,1026,324),
        (1038,1054,366),(994,1011,399),(1022,1038,458),
        (1520,1547,331),(1487,1517,375),(1489,1516,385),
        (1540,1576,375),(1518,1548,407),(1567,1591,407),(1551,1579,428),
        (1684,1703,399),
    ]
    floating_platforms = []
    for i, (x1,x2,y) in enumerate(platform_specs):
        c1,c2,row = _stamp_surface(grass,x1,x2,y,THIN)
        wx,wz = cell_world(c1,row)
        floating_platforms.append({"id":f"Step_{i+1:02d}","image":[x1,x2,y],"column_start":c1,"column_end":c2,"row":row,"x":c1*CELL_SIZE,"topZ":wz,"width":(c2-c1)*CELL_SIZE,"height":CELL_SIZE/2})

    water_specs = [
        (461,445,659,510,"Main_west_basin"),
        (1465,445,1601,510,"Main_east_basin"),
        (339,365,365,404,"West_short_fall"),
        (462,405,489,445,"West_basin_fall"),
        (621,366,641,405,"Island_upper_fall"),
        (608,406,659,445,"Island_lower_fall"),
        (1128,305,1155,440,"Central_tall_fall"),
    ]
    water_rects = []
    for x1,y1,x2,y2,name in water_specs:
        c1,r1=cell(x1,y1);c2,r2=cell(x2,y2)
        for row in range(max(0,r1),min(HEIGHT,max(r1+1,r2))):
            for col in range(max(0,c1),min(WIDTH,max(c1+1,c2))):
                water[row*WIDTH+col]=WATER_SURFACE if row==r1 else WATER_FILL
        wx,topz=world(x1,y1);_,bottomz=world(x2,y2)
        water_rects.append({"name":name,"image":[x1,y1,x2,y2],"x":wx,"topZ":topz,"bottomZ":bottomz,"width":(x2-x1)*SCALE,"height":(y2-y1)*SCALE,"type":"waterfall" if "fall" in name.lower() else "basin","collision":False})

    tree_specs=[
        (22,447,55,29),(176,319,75,43),(327,350,44,40),(385,359,76,41),
        (450,394,57,36),(615,351,92,50),(673,380,57,42),
        (711,311,44,36),(744,418,61,47),(794,360,66,39),
        (846,360,44,34),(901,360,117,48),(939,434,73,41),
        (955,287,73,37),(1047,203,33,41),(1105,252,58,47),
        (1194,305,82,53),(1270,270,77,51),(1345,270,60,41),
        (1403,270,45,29),(1446,326,66,42),(1600,319,47,37),
        (1646,319,53,41),(1737,341,56,40),(1767,341,73,51),
        (1794,439,79,53),(2010,439,105,55),
    ]
    trees=[_object("tree",x,y,height=h*SCALE,width=w*SCALE,variant=i%3,depth=20) for i,(x,y,h,w) in enumerate(tree_specs)]
    bush_specs=[
        (12,174,28),(106,298,31),(131,433.2,23),(152,416.1333333333,44),(205,319,42),
        (239,319,38),(267,416.1333333333,20),(307,404,34),(393,440,41),(477,405,22),
        (580,351,25),(644,406,31),(704,380,40),(740,311,43),(827,360,26),
        (899,434,47),(986,203,26),(1083,252,27),(1247,270,53),
        (1303,270,40),(1358,270,35),(1404,286,47),(1454,326,26),
        (1625,319,43),(1686,319,51),(1693,411,22),(1761,409,25),
        (1833,439,53),(1927,439,65),(1969,439,49),(2040,439,18),
    ]
    bushes=[_object("bush",x,y,width=w*SCALE,height=w*SCALE*0.46,variant=i%3) for i,(x,y,w) in enumerate(bush_specs)]
    # Rocks are source-pack assemblies, not newly painted or external images.
    rock_specs=[(207,319,45),(704,380,30),(742,311,53),(902,360,54),(1083,252,20),(1242,270,40),(1310,270,44),(1398,286,52),(1625,319,48),(1688,319,41),(1828,439,45),(1926,439,75)]
    rocks=[_object("rock_cluster",x,y,width=w*SCALE,height=w*SCALE*0.55,variant=i%3) for i,(x,y,w) in enumerate(rock_specs)]
    coins=[]
    for x,y in [(57,283),(131,281),(161,308),(305,339),(329,337),(574,337),(1016,310),(1695,381)]:
        col,row=cell(x,y)
        if 0<=col<WIDTH and 0<=row<HEIGHT:
            decor[row*WIDTH+col]=GEM
            coins.append(_object("gem",x,y,column=col,row=row))
    spike_specs=[(43,447,23),(173,416.1333333333,22),(344,404,20),(622,406,20),(946,287,19),(1073,440,20)]
    spikes=[]
    for i,(x,y,w) in enumerate(spike_specs):
        c1,row=cell(x,y);c2,_=cell(x+w,y)
        # Snap to a traced standing surface to ensure these sit ON grass.
        for col in range(c1,max(c1+1,c2)):
            if 0<=col<WIDTH and 1<=row<HEIGHT:
                grass[row*WIDTH+col]=GRASS
                decor[(row-1)*WIDTH+col]=SPIKE
        spikes.append({"id":f"GrassSpikes_{i+1:02d}","image":[x,y,w],"column_start":c1,"column_end":max(c1+1,c2),"ground_row":row,"z":(ORIGIN_ROW-row)*CELL_SIZE,"visual_only":True})
    props=[]
    for x,y in [(214,416.1333333333),(525,374),(791,418),(846,434),(1184,364),(1356,396),(1557,375)]:
        col,row=cell(x,y)
        if 0<=col<WIDTH and 1<=row<HEIGHT:
            decor[(row-1)*WIDTH+col]=CRATE
            props.append(_object("crate",x,y,column=col,row=row-1))

    layout={"name":"ReferenceLandscape120m","width":WIDTH,"height":HEIGHT,"tile_size":TILE_SIZE,"ppu":PPU,"cell_size":CELL_SIZE,"origin_row":ORIGIN_ROW,"span_cm":SPAN_CM,"reference_canvas":[REFERENCE_WIDTH,REFERENCE_HEIGHT],"reference_base_y":REFERENCE_BASE_Y,"ground":ground,"backdrop_ground":backdrop,"grass":grass,"decor":decor,"water":water,"polygons":polygons,"surfaces":surfaces,"floating_platforms":floating_platforms,"water_rects":water_rects,"trees":trees,"bushes":bushes,"rocks":rocks,"coins":coins,"spikes":spikes,"props":props,"collision_layer_names":["TerrainCollision","SurfaceCollision"],"source_atlas":"Simplified Platformer Pack/Tilesheet/platformPack_tilesheet.png","notes":["Hand traced from user supplied reference; no third tier or doors added.","Rear soil has no collision; its cap and the steps in front of it have collision.","Water and hazards are visual placement; character swimming, damage and traversal are not implemented.","Horizontal terrain span is exactly 12000cm; traversal time needs character tuning/playtesting."],"start":_object("start_marker",14,174),"finish":_object("finish_marker",2026,439)}
    layout['start']=_object('start_marker',28,447,baseZ=350.0)
    layout['start_stair_heights_cm']=[350,450,550,600]
    layout["validation"]=validate(layout)
    return layout


def validate(layout):
    arrays=[layout[k] for k in ("ground","backdrop_ground","grass","decor","water")]
    assert all(len(a)==WIDTH*HEIGHT for a in arrays)
    assert all(0<=v<=98 for a in arrays for v in a)
    assert layout["span_cm"]==12000
    for hazard in layout["spikes"]:
        for col in range(hazard["column_start"],hazard["column_end"]):
            r=hazard["ground_row"]
            assert layout["grass"][r*WIDTH+col]==GRASS
            assert layout["decor"][(r-1)*WIDTH+col]==SPIKE
    assert sum(r["type"]=="basin" for r in layout["water_rects"])==2
    assert sum(r["type"]=="waterfall" for r in layout["water_rects"])==5
    assert len(layout["floating_platforms"])==24
    return {"passed":True,"span_cm":12000,"grid":[WIDTH,HEIGHT],"polygons":len(layout["polygons"]),"surfaces":len(layout["surfaces"]),"stepping_platforms":len(layout["floating_platforms"]),"trees":len(layout["trees"]),"bushes":len(layout["bushes"]),"spike_groups":len(layout["spikes"]),"water_basins":2,"waterfalls":5,"player_playtest":False}


def to_tiled(layout=None, include_water=True):
    layout=layout or make_layout()
    def objects(index):
        half=index==28
        return {"objectgroup":{"objects":[{"id":1,"name":"Solid","type":"","x":0,"y":-16 if half else 0,"width":64,"height":32 if half else 64,"rotation":0,"visible":True}]}}
    specs=[("Backdrop_NoCollision","backdrop_ground"),("TerrainCollision","ground"),("SurfaceCollision","grass")]
    if include_water: specs.append(("Water_NoCollision","water"))
    specs.append(("Decoration_NoCollision","decor"))
    return {"version":1,"orientation":"orthogonal","renderorder":"right-down","width":WIDTH,"height":HEIGHT,"tilewidth":TILE_SIZE,"tileheight":TILE_SIZE,"nextobjectid":2,"tilesets":[{"firstgid":1,"name":"TS_FinalReference","image":"platformPack_tilesheet.png","imagewidth":896,"imageheight":448,"tilewidth":64,"tileheight":64,"margin":0,"spacing":0,"tiles":{str(i):objects(i) for i in (0,3,28)}}],"layers":[{"name":name,"type":"tilelayer","width":WIDTH,"height":HEIGHT,"x":0,"y":0,"visible":True,"opacity":1,"data":layout[key]} for name,key in specs]}


def write_layout(directory):
    dest=Path(directory);dest.mkdir(parents=True,exist_ok=True)
    layout=make_layout()
    (dest/"reference_layout.json").write_text(json.dumps(layout,ensure_ascii=False,indent=2),encoding="utf-8")
    (dest/"TM_FinalReference120m.json").write_text(json.dumps(to_tiled(layout),ensure_ascii=False),encoding="utf-8")
    return layout["validation"]


if __name__=="__main__":
    import sys
    print(json.dumps(write_layout(sys.argv[1] if len(sys.argv)>1 else Path(__file__).parent/"reference_layout_output"),ensure_ascii=False))
