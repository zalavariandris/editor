# Bug FIX
- crash without pointlight
- set number of lights in shader

# API improvements
- [ ] RenderPass.create_texture, create_fbo, create_program
- [x] twoline viewer eg:

  ```
  viewer = Viewer(scene)
  viewer.run(in_background=True)
  ```

# Features
- [ ] Viewer with multiple renderers (Matcap, PBR)
- [ ] support material textures
- [ ] support normal mapping