with window:
    """SETUP"""
    # IBL
    CUBEMAP     = renderpass(shaders=*glsl("equarectangular_to_cubemap"), environment_map)
    IRRADIANCE  = renderpass(shaders=*glsl("irradiance"), CUBEMAP)
    PREFILTER   = renderpass(shaders=*glsl("prefilter"), CUBEMAP)
    BRDF        = renderpass(shaders=*glsl("brdf"))

while window.running(vsync=True): ???
    """DRAW"""
    # Render
    SKYBOX      = renderpass(shaders=*glsl("skybox", camera, CUBEMAP))
    G_BUFFER    = renderpass(shaders=*glsl("geometry_pass"), camera, scene)

    PBR         = renderpass(shaders=*glsl("PBRLighting"), 
                             lights=lights,
                             gBuffer=G_BUFFER,
                             irradiance=IRRADIANCE,
                             prefilter=PREFILER,
                             brdf=BRDF)

    BEAUTY      = renderpass(shaders=*glsl("merge"), 
                             A=SKYBOX, 
                             B=PBR)
    
    # Post processing
    HIGHLIGHTS  = renderpass(shaders=*glsl("cutoff_highlights"),
                             input=BEAUTY)
    LDR         = renderpass(shaders=*glsl("tonemapping"),
                             input=BEAUTY,
                             exposure=1.0)
    final       = renderpass(shaders=*glsl("add"),
                             A=LDR,
                             B=HIGHLIGHTS)

    # Draw final image
    imdraw.texture(final, (0,0, width, height))

    # Debug
    gPosition, gNormal, gAlbedo = G_BUFFER
    imdraw.texture(gPosition,   (0,0, width, height))
    imdraw.texture(gNormal,     (0,0, width, height))
    imdraw.texture(gAlbedo,     (0,0, width, height))

    imdraw.texture(IRRADIANCE,  (0,0, width, height))
    imdraw.texture(PREFILER,    (0,0, width, height))
    imdraw.texture(BRDF,        (0,0, width, height))
