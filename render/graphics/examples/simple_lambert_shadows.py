if __name__ == "__main__":
    from OpenGL.GL import *
    import glm
    from editor.render.graphics.examples.viewer import Viewer
    from editor.render import glsl, puregl, imdraw
    from editor.render.graphics import Scene, Mesh, Geometry, Material, PointLight, SpotLight, DirectionalLight

    viewer = Viewer()


    scene = Scene()
    cube = Mesh(geometry=Geometry(*imdraw.geo.cube()), transform=glm.translate(glm.mat4(1), (0,0.5,0)))
    scene.add_child(cube)
    plane = Mesh(geometry=Geometry(*imdraw.geo.plane()))
    scene.add_child(plane)
    # dirlight = DirectionalLight(direction=glm.vec3(1, -6, -2),
    #                             color=glm.vec3(1.0),
    #                             intensity=1.0,
    #                             position=-glm.vec3(1, -6, -2),
    #                             radius=5,
    #                             near=1,
    #                             far=30)
    # scene.add_child(dirlight)

    spotlight = SpotLight(position=glm.vec3(-1, 0.5, -3),
                          direction=glm.vec3(1, -0.5, 3),
                          color=glm.vec3(0.04, 0.6, 1.0),
                          intensity=150.0,
                          fov=60,
                          near=1,
                          far=15)
    scene.add_child(spotlight)

    pointlight = PointLight(position=glm.vec3(2.5, 1.3, 2.5),
                            color=glm.vec3(1, 0.7, 0.1),
                            intensity=17.5,
                            near=0.1,
                            far=10)
    scene.add_child(pointlight)
    
    @viewer.event
    def on_setup():
        global lambert_program
        lambert_program = puregl.program.create(
        """#version 330 core
        layout (location=0) in vec3 position;
        layout (location=1) in vec2 uv;
        layout (location=2) in vec3 normal;

        uniform mat4 projection;
        uniform mat4 view;
        uniform mat4 model;

        out vec3 Normal;
        out vec3 Position;

        void main(){
            Normal = normal;
            Position = vec3(model * vec4(position, 1.0)).xyz;
            gl_Position = projection * view * model * vec4(position, 1.0);
        }
        """,

        """#version 330 core
        #define MAX_LIGHTS 3
        #define MAX_SHADOWMAPS 2
        #define MAX_SHADOWCUBES 1

        struct Light{
            int type;
            vec3 color;
            vec3 position;
            vec3 direction;
            float cutOff;
            mat4 matrix;
            int shadowIdx;

            float nearPlane;
            float farPlane;
        };
        
        uniform Light lights[MAX_LIGHTS];
        uniform sampler2D shadowMaps[MAX_SHADOWMAPS];
        uniform samplerCube shadowCubes[MAX_SHADOWCUBES];

        uniform vec3 color;
        in vec3 Position;
        in vec3 Normal;
        out vec4 FragColor;
        void main(){
            vec3 N = normalize(Normal);

            vec3 Lo=vec3(0);
            vec3 surfacePosition = Position;
            for(int i=0; i<MAX_LIGHTS; i++){
                float lightStrength = 0;
                vec3 L=vec3(0);
                if(lights[i].type==0)
                {
                    L = normalize(-lights[i].direction);
                    lightStrength=1.0;
                }
                else if(lights[i].type==1)
                {
                    L = normalize(lights[i].position - surfacePosition);
                    float distance = length(lights[i].position - surfacePosition);
                    lightStrength = 1.0 / (distance*distance);

                    // spotlight cutoff
                    if(lights[i].cutOff>=0)
                    {
                        float theta = dot(L, normalize(-lights[i].direction));
                        if(theta<lights[i].cutOff){
                            lightStrength=0.0;
                        }
                    }
                }
                else if(lights[i].type==2){
                    L = normalize(lights[i].position-surfacePosition);
                    // Calc light luminance
                    float distance = length(lights[i].position-surfacePosition);
                    lightStrength = 1.0 / (distance * distance);

                    // Mask luminance with shadow
                    float shadowDepth = texture(shadowCubes[lights[i].shadowIdx], -L).r;
                    shadowDepth*=lights[i].farPlane;
                    float surfaceDepth = length(lights[i].position-surfacePosition);
                    float bias=0.0;
                    float shadow = surfaceDepth-bias > shadowDepth ? 0.0 : 1.0;
                    lightStrength*=shadow;
                }else{
                    continue;
                }

                // Accumulate surface reflectance
                vec3 radiance = lights[i].color * lightStrength;

                float NdotL = max(dot(N, L), 0.0000001);
                Lo+=max(NdotL,0.0)*radiance*lightStrength;
            }


            float ambient = 0.1;
            FragColor = vec4(ambient+Lo, 1.0);
        }
        """)

    @viewer.event
    def on_draw():
        # render each shadowmap:
        for light in scene.lights():
            light.shadowmap.render(scene.meshes(), light.camera)

        # render scene
        glEnable(GL_DEPTH_TEST)
        glCullFace(GL_BACK)
        glViewport(0,0,viewer.width, viewer.height)
        with puregl.program.use(lambert_program):
            puregl.program.set_uniform(lambert_program, "projection", viewer.camera.projection)
            puregl.program.set_uniform(lambert_program, "view", viewer.camera.view)
            puregl.program.set_uniform(lambert_program, "model", glm.mat4(1))
            puregl.program.set_uniform(lambert_program, "color", (1,1,1))

            # set each light uniforms
            for i, light in enumerate(scene.lights()):
                if isinstance(light, PointLight):
                    puregl.program.set_uniform(lambert_program, "lights[{}].type".format(i), 2)
                    puregl.program.set_uniform(lambert_program, "lights[{}].position".format(i), light.position)
                    puregl.program.set_uniform(lambert_program, "lights[{}].color".format(i), light.color*light.intensity)
                if isinstance(light, SpotLight):
                    pass

            # set each shadowmap
            # - pointlight
            for i, light in enumerate(scene.lights()):
                shadowCubeIdx=0
                shadowMapIdx=0
                if isinstance(light, PointLight):
                    glActiveTexture(GL_TEXTURE0+0)
                    glBindTexture(GL_TEXTURE_CUBE_MAP, light.shadowmap.texture)
                    
                    puregl.program.set_uniform(lambert_program, "lights[{}].farPlane".format(i), float(light.far))

                    puregl.program.set_uniform(lambert_program, "lights[{}].shadowIdx".format(i), shadowCubeIdx)
                    puregl.program.set_uniform(lambert_program, "shadowCubes[{}]".format(shadowCubeIdx), 0)
                    shadowCubeIdx += 1

            # draw each geometry
            for mesh in scene.meshes():
                puregl.program.set_uniform(lambert_program, "model", mesh.transform)
                mesh.geometry._draw(lambert_program)

    viewer.start()