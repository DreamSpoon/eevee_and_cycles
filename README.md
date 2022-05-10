# Blender addon: EEVEE and Cycles
Easy buttons to combine/composit Blender's main render engines: EEVEE and Cycles.
Tested with Blender version 3.1, and theoretically works with Blender versions back to version 2.8

EEVEE scenes can be composited with Cycles scenes, and there are many different ways to do this.
Blender EEVEE and Cycles addon creates a simple setup, with either Cycles or EEVEE given priority in the compositor with the Z-combine node.

Buttons and options for this Blender addon are located in:
- View 3D -> Tools menu -> EEVEEandC
  - setting up the ViewLayers and splitting scene into EEVEE scene and Cycles scene
- Shader Editor -> Tools menu -> EEVEEandC
  - one button to add Transparent effect to EEVEE materials, because the ViewLayer Transparent option is not currently available in EEVEE Render Engine

## Summary
EEVEE objects can be made to render as Transparent/Holdout when a scene is rendered in Cycles, and
Cycles objects can be made to render as Transparent/Holdout when a scene is rendered in  EEVEE, so that
Objects can be selectively assigned EEVEE or Cycles render engine as needed.

e.g. Complex curved reflective / refractive surfaces, which are usually impossible/impractical to render in EEVEE, can be rendered in Cycles and then composited into EEVEE renders
This works even if the different EEVEE and Cycles objects overlap/intersect, but may require usage of Transparent instead of Holdout.

This addon uses the term "Opaque" instead of "Transparent", and "Holdin" and instead of "Holdout".
Opaque is non-Transparent and Holdin is non-Holdout. This is intended to make the process more intuitive.
- "Cycles Holdin" objects will render as:
  - regular in Cycles
  - Holdout in EEVEE
- "EEVEE Holdin" objects will render as:
  - Holdout in Cycles
  - regular in EEVEE
- "Cycles Opaque" objects will render as:
  - regular in Cycles
  - Transparent in EEVEE
  - *IMPORTANT NOTE: Objects moved into the Cycles Opaque collection will need to have their materials 'fixed' later with 'EEVEE Transparent Simple' button in the Shader Editor*
- "EEVEE Opaque" objects will render as:
  - Transparent in Cycles
  - regular in EEVEE

### Notes
- scene that uses Cycles render engine needs Film -> Transparent to be enabled for Holdout to work properly when rendering the Cycles scene
- Holdout works correctly in EEVEE render engine, even if Film -> Transparent is disabled
  - this is useful for including HDRI backgrounds / environments in final composit
- ViewLayer Transparent option is not currently available in EEVEE Render Engine

## To Use this Addon
To begin, press the 'Init ViewLayers' button first.
  - this will set up two separate ViewLayers for EEVEE and Cycles
  - 4 collections will be created (if they don't already exist), to help sort objects by render engine and visibility

Next, press the Split Scene by Engine button.
  - this creates two scenes, so that the ViewLayers can use different render engines

Then sort objects in your scene into the different collections (the 4 created by the 'Init ViewLayers' button) as needed.
  - Objects that are difficult/impractical to render properly in EEVEE should be put in the Cycles Holdin collection
  - Objects that are simple and fast to render properly in EEVEE should be put in the EEVEE Holdin collection
  - the EEVEE Opaque collection works automatically, but the Cycles Opaque collection is more work for the user, so the above instructions make use of the Holdin collections
    - ViewLayer Transparent option is not currently available in EEVEE Render Engine
  - *IMPORTANT NOTE: Objects moved into the Cycles Opaque collection will need to have their materials 'fixed' later with 'EEVEE Transparent Simple' button in the Shader Editor*
  - to get better results in final renders/composits, use 'Opaque' collections instead of 'Holdin' collections
	- 'Holdin' objects might have black outlines (similar to a "wireframe" effect) where EEVEE and Cycles pixels come together
    - 'Opaque' collections solve this "black outline" problem, but these collections are a bit more complicated to use

To render, or see how your objects will appear in their ViewLayer (EEVEE and Cycles objects viewed separately), switch to the scene for the "on top" render engine and switch ViewLayer to the "on top" ViewLayer.
  - if Cycles is "on top", then switch to the Cycles scene (usually named Cycles_Scene) and the Cycles ViewLayer (usually named Cycles_ViewLayer)
  - or, if EEVEE is "on top", then switch to the EEVEE scene (usually named EEVEE_Scene) and the EEVEE ViewLayer (usually named EEVEE_ViewLayer)

## Buttons and options

### Main Option - Cycles on Top
If enabled then Cycles is the top layer and EEVEE is the bottom layer.
If disabled then EEVEE is the top layer and Cycles is the bottom layer.
Top layer is composited above bottom layer by Z Combine node (theoretically).

### View3D Tools - Init ViewLayers button
Press this button first to initialize ViewLayers for EEVEE and Cycles.
Each Render Engine can later be automatically assigned a separate ViewLayer in a separate scene, by pressing the 'Split Scene by Engine' button.

### View3D Tools - Split Scene by Engine button
Use the 'Init ViewLayers' button BEFORE using this button.
Initialize other scene, with the opposite rendering engine (based on option Cycles on Top).

### View3D Tools - Init Compositor button
Initialize final compositor node tree for merging EEVEE and Cycles.
This button is usually not needed if the 'Init ViewLayers' and 'Split Scene by Engine' buttons have already been pressed.

### Shader Editor - EEVEE Transparent Simple button
Select a 'Material Output' node, and press this button. Output will be split, so the material will render as transparent in EEVEE and regular in Cycles.
When this button is used, each selected Material Output (non-EEVEE Material Outputs only) will have a few nodes added to make the material render as Transparent (only to the camera) in EEVEE, while still rendering as regular in Cycles.
This is a workaround because the Transparent option is not automatically available to collections in EEVEE.
