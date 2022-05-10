# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy

SCENE_NAME_EEVEE = "EEVEE_Scene"
SCENE_NAME_CYCLES = "Cycles_Scene"

VIEWLAYER_NAME_EEVEE = "EEVEE_ViewLayer"
VIEWLAYER_NAME_CYCLES = "Cycles_ViewLayer"

COLLECTION_NAME_EEVEE_HOLDIN = "EEVEE_Holdin"
COLLECTION_NAME_CYCLES_HOLDIN = "Cycles_Holdin"
COLLECTION_NAME_EEVEE_OPAQUE = "EEVEE_Opaque"
COLLECTION_NAME_CYCLES_OPAQUE = "Cycles_Opaque"
COLL_HOLDIN = "Holdin"
COLL_OPAQUE = "Opaque"
ENG_EEVEE = "EEVEE"
ENG_CYCLES = "Cycles"
COLLECTION_NAMES_ALL = {
    COLLECTION_NAME_EEVEE_HOLDIN: (ENG_EEVEE, COLL_HOLDIN),
    COLLECTION_NAME_CYCLES_HOLDIN: (ENG_CYCLES, COLL_HOLDIN),
    COLLECTION_NAME_EEVEE_OPAQUE: (ENG_EEVEE, COLL_OPAQUE),
    COLLECTION_NAME_CYCLES_OPAQUE: (ENG_CYCLES, COLL_OPAQUE),
}

RENDER_ENGINE_CYCLES = "CYCLES"
RENDER_ENGINE_EEVEE = "BLENDER_EEVEE"

SETTINGS_FIX_TYPE = {
    ("CLIP", "Alpha Clip", "Binary visibility"),
    ("HASHED", "Alpha Hashed", "Noise dithered binary visibility"),
    ("BLEND", "Alpha Blend", "Polygon transparent from alpha channel")
}

def init_viewlayer(context, cycles_top):
    # ensure that EEVEE and Cycles view layers exist, re-using current layer as needed
    scn = context.scene
    eevee_layer = scn.view_layers.get(VIEWLAYER_NAME_CYCLES)
    cycles_layer = scn.view_layers.get(VIEWLAYER_NAME_CYCLES)
    if cycles_layer is None:
        the_vl = None
        if cycles_top:
            context.view_layer.name = VIEWLAYER_NAME_CYCLES
            the_vl = context.view_layer
        else:
            the_vl = scn.view_layers.new(VIEWLAYER_NAME_CYCLES)
        # ensure that this viewlayer's Z pass is delivered to compositor 
        the_vl.use_pass_z = True
    if eevee_layer is None:
        the_vl = None
        if not cycles_top:
            context.view_layer.name = VIEWLAYER_NAME_EEVEE
            the_vl = context.view_layer
        else:
            the_vl = scn.view_layers.new(VIEWLAYER_NAME_EEVEE)
        # ensure that this viewlayer's Z pass is delivered to compositor 
        the_vl.use_pass_z = True

def init_collections(scene):
    for coll_name in COLLECTION_NAMES_ALL:
        test_c = bpy.data.collections.get(coll_name)
        # if collection doesn't exist then create it and link to main scene collection
        if test_c is None:
            new_coll = bpy.data.collections.new(name=coll_name)
            scene.collection.children.link(new_coll)

    # set collection holdout and transparent settings separately for EEVEE and Cycles viewlayers
    for vlayer in scene.view_layers:
        if vlayer.name == VIEWLAYER_NAME_EEVEE:
            search_layer_collections(vlayer.layer_collection, True, False)
        elif vlayer.name == VIEWLAYER_NAME_CYCLES:
            search_layer_collections(vlayer.layer_collection, False, True)

def search_layer_collections(layer_coll, is_eevee_layer, is_cycles_layer):
    test = COLLECTION_NAMES_ALL.get(layer_coll.name)
    if test != None:
        if test[0] == ENG_EEVEE:
            if test[1] == COLL_HOLDIN:
                if is_eevee_layer:
                    layer_coll.holdout = False
                elif is_cycles_layer:
                    layer_coll.holdout = True
            elif test[1] == COLL_OPAQUE:
                if is_eevee_layer:
                    layer_coll.indirect_only = False
                elif is_cycles_layer:
                    layer_coll.indirect_only = True
        elif test[0] == ENG_CYCLES:
            if test[1] == COLL_HOLDIN:
                if is_eevee_layer:
                    layer_coll.holdout = True
                elif is_cycles_layer:
                    layer_coll.holdout = False
            elif test[1] == COLL_OPAQUE:
                if is_eevee_layer:
                    layer_coll.indirect_only = True
                elif is_cycles_layer:
                    layer_coll.indirect_only = False

    # recursively search sub-collections
    for child_coll in layer_coll.children:
        search_layer_collections(child_coll, is_eevee_layer, is_cycles_layer)

def show_outliner_columns():
    # Fetch the first outliner area in the screen
    # Will throw error if workspace doesn't contain any outliner editor.
    try:
        outliner_area = next(a for a in bpy.context.screen.areas if a.type == "OUTLINER")
    except:
        return
    
    space = outliner_area.spaces[0]
    space.show_restrict_column_holdout = True
    space.show_restrict_column_indirect_only = True

class EANDC_InitViewLayers(bpy.types.Operator):
    bl_idname = "e_and_c.init_viewlayers"
    bl_description = "Press this button first to Initialize ViewLayers for EEVEE and Cycles. Each Render Engine " \
        "can later be assigned a separate ViewLayer in a separate scene, by pressing the 'Split Scene by Engine' button"
    bl_label = "Init ViewLayers"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scn = context.scene
        init_viewlayer(context, scn.EANDC_CyclesTop)
        init_collections(scn)
        if scn.EANDC_ShowOutlinerColumnsHT:
            show_outliner_columns()
        return {'FINISHED'}

def init_final_compositor(eevee_scene, cycles_scene, cycles_top, clear_previous):
    top_scene = eevee_scene
    if cycles_top:
        top_scene = cycles_scene

    # get compositor node tree
    top_scene.use_nodes = True
    tree_nodes = top_scene.node_tree.nodes
    if clear_previous:
        tree_nodes.clear()

    new_nodes = {}

    # material shader nodes
    node = tree_nodes.new(type="CompositorNodeRLayers")
    node.name = "Cycles Render Layers"
    node.label = ""
    node.width = 240
    node.height = 100
    node.location = (-180, 250)
    if cycles_scene != None:
        node.scene = cycles_scene
    if top_scene.view_layers.get(VIEWLAYER_NAME_CYCLES):
        node.layer = VIEWLAYER_NAME_CYCLES
    new_nodes["Cycles Render Layers"] = node

    node = tree_nodes.new(type="CompositorNodeRLayers")
    node.name = "EEVEE Render Layers"
    node.label = ""
    node.width = 240
    node.height = 100
    node.location = (-180, -150)
    if eevee_scene != None:
        node.scene = eevee_scene
    if top_scene.view_layers.get(VIEWLAYER_NAME_EEVEE):
        node.layer = VIEWLAYER_NAME_EEVEE
    new_nodes["EEVEE Render Layers"] = node

    node = tree_nodes.new(type="CompositorNodeZcombine")
    node.name = "Z Combine"
    node.label = ""
    node.width = 140
    node.height = 100
    node.location = (235, 100)
    node.use_alpha = True
    node.use_antialias_z = True
    new_nodes["Z Combine"] = node

    node = tree_nodes.new(type="CompositorNodeComposite")
    node.name = "Composite"
    node.label = ""
    node.width = 140
    node.height = 100
    node.location = (600, 150)
    new_nodes["Composite"] = node

    tree_links = top_scene.node_tree.links
    if cycles_top:
        # Cycles on top for the inputs to the Z combine node
        tree_links.new(new_nodes["Cycles Render Layers"].outputs[0], new_nodes["Z Combine"].inputs[0])
        tree_links.new(new_nodes["EEVEE Render Layers"].outputs[0], new_nodes["Z Combine"].inputs[2])
        tree_links.new(new_nodes["Cycles Render Layers"].outputs[2], new_nodes["Z Combine"].inputs[1])
        tree_links.new(new_nodes["EEVEE Render Layers"].outputs[2], new_nodes["Z Combine"].inputs[3])
    else:
        # EEVEE on top for the inputs to the Z combine node
        tree_links.new(new_nodes["Cycles Render Layers"].outputs[0], new_nodes["Z Combine"].inputs[2])
        tree_links.new(new_nodes["EEVEE Render Layers"].outputs[0], new_nodes["Z Combine"].inputs[0])
        tree_links.new(new_nodes["Cycles Render Layers"].outputs[2], new_nodes["Z Combine"].inputs[3])
        tree_links.new(new_nodes["EEVEE Render Layers"].outputs[2], new_nodes["Z Combine"].inputs[1])
    tree_links.new(new_nodes["Z Combine"].outputs[1], new_nodes["Composite"].inputs[2])
    tree_links.new(new_nodes["Z Combine"].outputs[0], new_nodes["Composite"].inputs[0])

class EANDC_InitFinalCompositor(bpy.types.Operator):
    bl_idname = "e_and_c.init_final_compositor"
    bl_description = "Initialize final compositor node tree for merging EEVEE and Cycles. This button is " \
        "usually not needed if the 'Init ViewLayers' and 'Split Scene by Engine' buttons have already been pressed"
    bl_label = "Init Compositor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scn = context.scene
        # ensure Z pass is available for the view layers
        eevee_layer = scn.view_layers.get(VIEWLAYER_NAME_EEVEE)
        if eevee_layer != None:
            eevee_layer.use_pass_z = True
        cycles_layer = scn.view_layers.get(VIEWLAYER_NAME_CYCLES)
        if cycles_layer != None:
            cycles_layer.use_pass_z = True
        if scn.EANDC_CyclesTop:
            init_final_compositor(None, scn, scn.EANDC_CyclesTop, scn.EANDC_ClearPreviousCompositTree)
        else:
            init_final_compositor(scn, None, scn.EANDC_CyclesTop, scn.EANDC_ClearPreviousCompositTree)
        return {'FINISHED'}

def split_scene_by_engine(current_scene, cycles_top, clear_other_composit_tree, add_film_transparent_current,
                          add_film_transparent_other):
    # name the current scene by render engine type
    if cycles_top:
        # if the name for the Cycles scene is taken then swap names to avoid Blender auto-renaming our current scene 
        if current_scene.name == SCENE_NAME_CYCLES:
            copy_current_scene = current_scene.copy()
            # push the already existing scene name to the end of the .xxx number system
            # e.g. CyclesScene.001 is auto-renamed by Blender to be CyclesScene.005
            current_scene.name = SCENE_NAME_CYCLES + ".001"
            # the scenes have now been swapped out, so swap the references
            current_scene = copy_current_scene
        # the scene gets the available name, after name swapping (if it was needed)
        current_scene.name = SCENE_NAME_CYCLES
    else:
        # if the name for the EEVEE scene is taken then swap names to avoid Blender auto-renaming our current scene 
        if current_scene.name == SCENE_NAME_EEVEE:
            # make a copy of current scene, before name swap
            copy_current_scene = current_scene.copy()
            # push the already existing scene name to the end of the .xxx number system
            # e.g. EeveeScene.001 is auto-renamed by Blender to be EeveeScene.005
            current_scene.name = SCENE_NAME_EEVEE + ".001"
            # the scenes have now been swapped out, so swap the references
            current_scene = copy_current_scene
        # the scene gets the available name, after name swapping (if it was needed)
        current_scene.name = SCENE_NAME_EEVEE

    # copy linked everything in the current scene to a new scene, for the opposite render engine
    new_other_scene = bpy.data.scenes[current_scene.name].copy()
    # get the new name for the other scene
    other_name = SCENE_NAME_CYCLES
    if cycles_top:
        other_name = SCENE_NAME_EEVEE

    # if new name has already been used, then rename the scene that used the name
    test_scene = bpy.data.scenes.get(other_name)
    if test_scene != None:
        # let Blender figure it out - this should automatically update usage of the scene name elsewhere
        test_scene.name = other_name + ".001"

    # rename the new other scene, after ensuring the name is available,
    # ensuring the name is available prevents Blender from auto-renaming the scene, which screws things up later 
    new_other_scene.name = other_name

    # see: https://blender.stackexchange.com/questions/155092/how-to-create-a-linked-copy-scene-in-python-without-using-ops
    # next line of code might not necessary, only there to prevent scene being added to Orphan Data
    new_other_scene.use_fake_user = True
    # assign render engines
    if cycles_top:
        current_scene.render.engine = RENDER_ENGINE_CYCLES
        new_other_scene.render.engine = RENDER_ENGINE_EEVEE
    else:
        current_scene.render.engine = RENDER_ENGINE_EEVEE
        new_other_scene.render.engine = RENDER_ENGINE_CYCLES
    if add_film_transparent_current:
        current_scene.render.film_transparent = True
    if add_film_transparent_other:
        new_other_scene.render.film_transparent = True

    # if needed, remove all nodes in the other scene's compositor tree
    if clear_other_composit_tree and new_other_scene.node_tree != None:
        new_other_scene.node_tree.clear()

    return new_other_scene

# the EEVEE scene must only render the EEVEE view layer
# the Cycles scene must only render the Cycles view layer
def modify_renderlayers_scene_separate(eevee_scene, cycles_scene):
    eevee_scene_cycles_layer = eevee_scene.view_layers.get(VIEWLAYER_NAME_CYCLES)
    cycles_scene_eevee_layer = cycles_scene.view_layers.get(VIEWLAYER_NAME_EEVEE)
    # disable the Cycles layer in the EEVEE scene
    if eevee_scene_cycles_layer != None:
        eevee_scene_cycles_layer.use = False
    # disable the EEVEE layer in the Cycles scene
    if cycles_scene_eevee_layer != None:
        cycles_scene_eevee_layer.use = False

class EANDC_SplitSceneByEngine(bpy.types.Operator):
    bl_idname = "e_and_c.split_scene_by_engine"
    bl_description = "Use the 'Init ViewLayers' button BEFORE using this button. Initialize other scene, with the " \
        "opposite rendering engine (based on Cycles on Top)"
    bl_label = "Split Scene by Engine"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scn = context.scene

        split_scene_by_engine(scn, scn.EANDC_CyclesTop, scn.EANDC_ClearOtherSceneCompositTree, scn.EANDC_AddFilmTransparentCurrent,
                          scn.EANDC_AddFilmTransparentOther)
        eevee_scene = bpy.data.scenes.get(SCENE_NAME_EEVEE)
        cycles_scene = bpy.data.scenes.get(SCENE_NAME_CYCLES)
        if scn.EANDC_AddCurrentSceneCompositTree:
            init_final_compositor(eevee_scene, cycles_scene, scn.EANDC_CyclesTop, scn.EANDC_ClearCurrentSceneCompositTree)
        modify_renderlayers_scene_separate(eevee_scene, cycles_scene)
        return {'FINISHED'}

def insert_eevee_transparent(context, insert_advanced, transparent_settings_fix):
    node_tree = context.space_data.edit_tree
    # search for selected Output Material nodes in the current node tree, and do insert EEVEE transparent with them
    for node in node_tree.nodes:
        if node.bl_idname == "ShaderNodeOutputMaterial" and node.select:
            if node.target != "EEVEE":
                tree_insert_eevee_transparent(node, node_tree, insert_advanced)
    if transparent_settings_fix:
        context.active_object.active_material.blend_method = transparent_settings_fix

# get output of the node 'node_from' that is linked to 'node_to'
# note: returns the 'output', not the 'output link'
def get_output_of_from_node(node_from, node_to):
    for output in node_from.outputs:
        for output_link in output.links:
            if output_link.to_node == node_to:
                return output
    return None

def tree_insert_eevee_transparent(node, existing_tree, insert_advanced):
    # if surface input link does not exist then skip it
    input_surface_node_output = None
    try:
        input_link_surface = node.inputs[0].links[0]
    except:
        pass
    else:
        input_surface_node = input_link_surface.from_node
        input_surface_node_output = get_output_of_from_node(input_surface_node, node)

    # if volume input link does not exist then skip it
    input_volume_node_output = None
    try:
        input_link_vol = node.inputs[1].links[0]
    except:
        pass
    else:
        input_volume_node = input_link_vol.from_node
        input_volume_node_output = get_output_of_from_node(input_volume_node, node)

    # if surface and volume inputs do not exist then quit: there is nothing to use as input for a new Material Output
    if input_surface_node_output is None and input_volume_node_output is None:
        return 

    new_nodes = {}
    start_x = node.location.x
    start_y = node.location.y

    tree_nodes = existing_tree.nodes
    # material shader nodes
    x_node = tree_nodes.new(type="ShaderNodeOutputMaterial")
    x_node.target = "EEVEE"
    x_node.location = (start_x+325, start_y-125)
    new_nodes["Material Output"] = x_node

    x_node = tree_nodes.new(type="ShaderNodeBsdfTransparent")
    x_node.location = (start_x-25, start_y-200)
    new_nodes["Transparent BSDF"] = x_node

    x_node = tree_nodes.new(type="ShaderNodeLightPath")
    x_node.location = (start_x-25, start_y-300)
    new_nodes["Light Path"] = x_node

    # links between nodes
    tree_links = existing_tree.links

    # create the links between the new Output Material node and the inputs to the old Output Material node
    if input_surface_node_output != None:
        x_node = tree_nodes.new(type="ShaderNodeMixShader")
        x_node.location = (start_x+150, start_y-150)
        new_nodes["Mix Shader Surface"] = x_node
        tree_links.new(new_nodes["Light Path"].outputs[0], x_node.inputs[0])
        tree_links.new(input_surface_node_output, new_nodes["Mix Shader Surface"].inputs[1])
        tree_links.new(new_nodes["Transparent BSDF"].outputs[0], new_nodes["Mix Shader Surface"].inputs[2])
        tree_links.new(new_nodes["Mix Shader Surface"].outputs[0], new_nodes["Material Output"].inputs[0])
    if input_volume_node_output != None:
        x_node = tree_nodes.new(type="ShaderNodeMixShader")
        x_node.location = (start_x+150, start_y-280)
        new_nodes["Mix Shader Volume"] = x_node
        tree_links.new(new_nodes["Light Path"].outputs[0], new_nodes["Mix Shader Volume"].inputs[0])
        # volume does not get "Transparent Input", it gets "Blank Input"
        tree_links.new(input_volume_node_output, new_nodes["Mix Shader Volume"].inputs[1])
        tree_links.new(new_nodes["Mix Shader Volume"].outputs[0], new_nodes["Material Output"].inputs[1])

    # re-position original Material Output node
    node.location.x = node.location.x + 325

    # if old node wasn't EEVEE then change it to Cycles, so "Output All" will become "Output Cycles" and
    # "Output EEVEE" will remain unchanged - a sort of a graceful fail
    if node.target != "EEVEE":
        node.target = "CYCLES"

class EANDC_EeveeTransparentSimple(bpy.types.Operator):
    bl_idname = "eandc.eevee_transparent_simple"
    bl_description = "Select a 'Material Output' node, and press button. Output will be split, so the material " \
        "will render as transparent in EEVEE and regular in Cycles"
    bl_label = "EEVEE Transparent Simple"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        s = context.space_data
        if s.type == 'NODE_EDITOR' and s.node_tree != None and \
            s.tree_type in ("ShaderNodeTree", "TextureNodeTree"):
            return True
        return False

    def execute(self, context):
        if context.scene.EANDC_EeveeTransparentSettingsFix:
            insert_eevee_transparent(context, False, context.scene.EANDC_EeveeTransparentSettingsFixType)
        else:
            insert_eevee_transparent(context, False, None)
        return {'FINISHED'}
