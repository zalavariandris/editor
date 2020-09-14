with window:
	"""SETUP"""
	# IBL
	CUBEMAP     = renderpass(shaders=*glsl("equarectangular_to_cubemap"), environment_map)
	IRRADIANCE  = renderpass(shaders=*glsl("irradiance"), cubemap)
	PREFILTER 	= renderpass(shaders=*glsl("prefilter"), cubemap)
	BRDF 		= renderpass(shaders=*glsl("brdf"))

while window.running(vsync=True): ???
	"""DRAW"""
	# Render
	G_BUFFER    = renderpass(shaders=*glsl("geometry_pass"), projection, view, draw_scene)

	BEAUTY		= renderpass(shaders=*glsl("PBR2"), 
							 lights=lights,
							 gBuffer=G_BUFFER,
							 irradiance=IRRADIANCE,
							 prefilter=PREFILER,
							 brdf=BRDF)
	
	# Post processing
	HIGHLIGHTS  = renderpass(shaders=*glsl("cutoff_highlights"),
			   				 input=BEAUTY)
	LDR			= renderpass(shaders=*glsl("tonemapping"),
			   				 input=BEAUTY,
			   				 exposure=1.0)
	final		= renderpass(shaders=*glsl("add"),
							 A=LDR,
							 B=HIGHLIGHTS)


	# Draw final image
	imdraw.texture(final, (0,0, width, height))

	# Debug
	gPosition, gNormal, gAlbedo = G_BUFFER
	imdraw.texture(gPosition,	(0,0, width, height))
	imdraw.texture(gNormal,		(0,0, width, height))
	imdraw.texture(gAlbedo,		(0,0, width, height))

	imdraw.texture(IRRADIANCE,	(0,0, width, height))
	imdraw.texture(PREFILER,	(0,0, width, height))
	imdraw.texture(BRDF, 		(0,0, width, height))
