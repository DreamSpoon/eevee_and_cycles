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

bl_info = {
    "name": "EEVEE and Cycles",
    "description": "Mix EEVEE and Cycles to get the best of both.",
    "author": "Dave",
    "version": (0, 9, 0),
    "blender": (2, 80, 0),
    "location": "View 3D -> Tools -> EEVEEandC",
    "category": "Rendering",
    "wiki_url": "https://github.com/DreamSpoon/eevee_and_cycles#readme",
}

import bpy
from bpy.props import (BoolProperty, EnumProperty)

from .e_and_c import (EANDC_InitViewLayers, EANDC_InitFinalCompositor, EANDC_SplitSceneByEngine,
    EANDC_EeveeTransparentSimple, SETTINGS_FIX_TYPE)

class EANDC_PT_ObjStuff(bpy.types.Panel):
    bl_label = "ViewLayer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "EEVEEandC"

    def draw(self, context):
        layout = self.layout
        scn = context.scene

        layout.label(text="Initialize")
        layout.prop(scn, "EANDC_CyclesTop")
        box = layout.box()
        box.operator(EANDC_InitViewLayers.bl_idname)
        box.prop(scn, "EANDC_ShowOutlinerColumnsHT")
        box.operator(EANDC_SplitSceneByEngine.bl_idname)
        box.label(text="Current Scene:")
        box.prop(scn, "EANDC_ClearOtherSceneCompositTree")
        box.prop(scn, "EANDC_AddCurrentSceneCompositTree")
        box.prop(scn, "EANDC_AddFilmTransparentCurrent")
        box.label(text="Other Scene:")
        row = box.row()
        row.active = scn.EANDC_AddCurrentSceneCompositTree
        row.prop(scn, "EANDC_ClearCurrentSceneCompositTree")
        box.prop(scn, "EANDC_AddFilmTransparentOther")
        box = layout.box()
        box.operator(EANDC_InitFinalCompositor.bl_idname)
        box.prop(scn, "EANDC_ClearPreviousCompositTree")

class EANDC_PT_MaterialStuff(bpy.types.Panel):
    bl_idname = "NODE_PT_material_stuff"
    bl_label = "EV and Cycles"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "EEVEEandC"

    def draw(self, context):
        layout = self.layout
        layout.operator(EANDC_EeveeTransparentSimple.bl_idname)
        #layout.operator(EANDC_EeveeTransparentAdvanced.bl_idname)
        layout.prop(context.scene, "EANDC_EeveeTransparentSettingsFix")
        layout.prop(context.scene, "EANDC_EeveeTransparentSettingsFixType")

classes = [
    EANDC_PT_ObjStuff,
    EANDC_InitViewLayers,
    EANDC_SplitSceneByEngine,
    EANDC_InitFinalCompositor,
    EANDC_PT_MaterialStuff,
    EANDC_EeveeTransparentSimple,
    #EANDC_EeveeTransparentAdvanced,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bts = bpy.types.Scene
    bts.EANDC_CyclesTop = BoolProperty(name="Cycles Top",
        description="If enabled then Cycles is the top layer and EEVEE is the bottom layer. If disabled then " +
        "EEVEE is the top layer and Cycles is the bottom layer. Top layer is composited above bottom layer " +
        "(Z Combine)", default=True)
    bts.EANDC_ShowOutlinerColumnsHT = BoolProperty(name="Show Outliner HT",
        description="Show Holdout and Transparent columns in the Outliner, for each collection", default=True)
    bts.EANDC_AddCurrentSceneCompositTree = BoolProperty(name="Add Current Scene Compositor Nodes",
        description="Add compositor nodes to this scene's composit tree. These compositor nodes will merge the " +
        "EEVEE and Cycles renders together", default=True)
    bts.EANDC_ClearCurrentSceneCompositTree = BoolProperty(name="Clear Current Scene Compositor Nodes",
        description="When Init Other Scene is used, and if this is enabled then remove all compositor nodes from " +
        "this scene before adding new compositor nodes to this scene", default=False)
    bts.EANDC_AddFilmTransparentCurrent = BoolProperty(name="Current Scene Film Transparent",
        description="With current scene, enable the Film, Transparent option in the Properties, Render panel when the 'Split Scene' button is used", default=False)
    bts.EANDC_ClearOtherSceneCompositTree = BoolProperty(name="Clear Other Scene Compositor Nodes",
        description="When Init Other Scene is used, and if this is enabled then remove all compositor nodes after " +
        "copying the scene", default=True)
    bts.EANDC_AddFilmTransparentOther = BoolProperty(name="Other Scene Film Transparent",
        description="With other scene, enable the Film, Transparent option in the Properties, Render panel when the 'Split Scene' button is used", default=True)
    bts.EANDC_ClearPreviousCompositTree = BoolProperty(name="Clear Compositor Nodes",
        description="Enable deleting of all compositor nodes when 'Init Compositor' and " +
        "'Init Pass Thru Compositor' buttons are used", default=False)
    bts.EANDC_EeveeTransparentSettingsFix = BoolProperty(name="Enable material EEVEE transparent",
        description="Enable Transparent to work correctly in EEVEE", default=True)
    bts.EANDC_EeveeTransparentSettingsFixType = EnumProperty(name="Alpha Blend Mode",
                    description="Mode of Alpha Blend to use for Transparent material. This only applies to EEVEE render engine",
                    items=SETTINGS_FIX_TYPE,
                    default="HASHED")

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.EANDC_EeveeTransparentSettingsFixType
    del bpy.types.Scene.EANDC_EeveeTransparentSettingsFix
    del bpy.types.Scene.EANDC_ClearPreviousCompositTree
    del bpy.types.Scene.EANDC_AddFilmTransparentOther
    del bpy.types.Scene.EANDC_ClearOtherSceneCompositTree
    del bpy.types.Scene.EANDC_AddFilmTransparentCurrent
    del bpy.types.Scene.EANDC_ClearCurrentSceneCompositTree
    del bpy.types.Scene.EANDC_AddCurrentSceneCompositTree
    del bpy.types.Scene.EANDC_ShowOutlinerColumnsHT
    del bpy.types.Scene.EANDC_CyclesTop

if __name__ == "__main__":
    register()
