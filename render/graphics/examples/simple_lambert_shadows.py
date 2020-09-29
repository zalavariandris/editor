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
    # scene.add_child(spotlight)

    pointlight = PointLight(position=glm.vec3(2.5, 1.3, 2.5),
                            color=glm.vec3(1, 0.7, 0.1),
                            intensity=17.5,
                            near=0.1,
                            far=10)
    scene.add_child(pointlight)
    
    @viewer.event
    def on_setup():
        global lambert_program
        vertex = """#version 330 core
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

        fragment="""#version 330 core
        // Lighting
        #define MAX_POINT_LIGHTS 3
        #define MAX_SPOT_LIGHTS 3
        #define MAX_DIR_LIGHTS 3

        uniform struct PointLight{
            vec3 color;
            float intensity;
            vec3 position;
            samplerCube shadowcube;
            float farPlane;
        } point_lights[MAX_POINT_LIGHTS];
        uniform int num_point_lights;

        vec3 calcRadiance(PointLight light, vec3 surfacePosition){
            vec3 lightPosition = light.position;
            vec3 L = normalize(lightPosition-surfacePosition);
            float dist = length(lightPosition-surfacePosition);
            float attenuation = 1.0 / (dist*dist);
            vec3 radiance = light.color * light.intensity * attenuation;

            // mask radiance with shadowmap
            float shadowDepth = texture(light.shadowcube, normalize(-L)).r*light.farPlane;
            float surfaceDepth = dist;
            float bias = 0.01;
            float shadow = surfaceDepth-bias > shadowDepth ? 1.0 : 0.0;
            radiance*=1-shadow;
            return radiance;
        }

        uniform vec3 color;
        in vec3 Position;
        in vec3 Normal;
        out vec4 FragColor;
        void main(){
            vec3 N = normalize(Normal);

            vec3 Lo=vec3(0);
            vec3 surfacePosition = Position;
            for(int i=0; i<num_point_lights; i++){
                // calculate light radiance at surface positions (Light Function)
                vec3 radiance = calcRadiance(point_lights[i], surfacePosition);

                // calculate surface reflectance (BRDF function)
                vec3 lightPosition = point_lights[i].position;
                vec3 L = normalize(lightPosition-surfacePosition);
                float NdotL = max(dot(N, L), 0.0000001);
                vec3 reflectance = max(NdotL,0.0)*radiance;

                // Accumulate surface reflectance
                Lo+=reflectance;
            }


            float ambient = 0.1;
            FragColor = vec4(ambient+Lo, 1.0);
        }
        """
        lambert_program = puregl.program.create(vertex, fragment)

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

            puregl.program.set_uniform(lambert_program, "num_point_lights", 1)
            # set each light uniforms
            for i, light in enumerate(scene.lights()):
                if isinstance(light, PointLight):
                    puregl.program.set_uniform(lambert_program, "point_lights[{}].type".format(i), 2)
                    puregl.program.set_uniform(lambert_program, "point_lights[{}].position".format(i), light.position)
                    puregl.program.set_uniform(lambert_program, "point_lights[{}].color".format(i), light.color)
                    puregl.program.set_uniform(lambert_program, "point_lights[{}].intensity".format(i), light.intensity)
                    # shadowmap
                    glActiveTexture(GL_TEXTURE0+0)
                    glBindTexture(GL_TEXTURE_CUBE_MAP, light.shadowmap.texture)
                    puregl.program.set_uniform(lambert_program, "point_lights[{}].shadowCube".format(i), 0)
                    puregl.program.set_uniform(lambert_program, "point_lights[{}].farPlane".format(i), float(light.far))

                if isinstance(light, SpotLight):
                    pass



            # draw each geometry
            for mesh in scene.meshes():
                puregl.program.set_uniform(lambert_program, "model", mesh.transform)
                mesh.geometry._draw(lambert_program)

    viewer.start()