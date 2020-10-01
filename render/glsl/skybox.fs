#version 330 core
out vec4 FragColor;
in vec3 vUvw;
uniform vec3 cameraPos;
uniform samplerCube skybox;
uniform bool groundProjection;

vec3 skyboxAtDirection(vec3 direction, bool groundProjection){
	vec3 Direction = normalize(vUvw);
	if(groundProjection)
	{
		vec3 Position = cameraPos;
		const vec3 GroundCenter = vec3(0,0,0);
		const float GroundRadius = 3; 
		
		if(Direction.y < 0.0){
			vec3 OrgDir = Direction;
			// Compute intersection with virtual ground plane
			float t = (GroundCenter[1] - Position[1])/Direction[1];
			vec3 GP = Position + Direction * t;

			// Compute virtual projection point rays are projecting from
			vec3 TP = GroundCenter + vec3(0, GroundRadius,0);
			// Use direction from that point to the groundplane as the
			// new virtual direction
			Direction = normalize(GP-TP);

			// Smoothen out the joint a bit....
			// Thanks to Vlado for suggestion!
			if (Direction[1] > -0.1)
			{
				float fac = 1.0 - Direction[1] * -10.0;
				fac *= fac;
				
				Direction = mix(Direction, OrgDir, fac);
			}
		}
	}
	return texture(skybox, Direction).rgb;
}

void main(){
	vec3 Direction = normalize(vUvw);
	FragColor = vec4(skyboxAtDirection(Direction, groundProjection),1.0);
}

/*
if (doBlur)
	Direction = OrgDir + (noise("hash", I, i) - 0.5) * BlurAmount / 100.0;

// Ground Projection mode is on, and direction is pointing down?
if (GroundProjection == 1 && Direction[2] < 0.0)
{
	// Compute intersection with virtual ground plane
	float t = (GroundCenter[2] - Position[2])/Direction[2];
	point GP = Position + Direction * t;
	
	// Assume we are doing the ground
	int   doGround = 1;

	// Special case for the viewport:	
	if (HLSLBackend)
	{
		// Detect if we are in the environment rendering
		// stage for Nitrous reflection maps. If so,
		// do not apply the special mapping ground mapping, 
		// just do regular spherical mapping....
		if (distance(GP, CP) < 1e-4)
			doGround = 0;
	}
	
	if (doGround)
	{
		// Compute virtual projection point rays are projecting from
		point TP = GroundCenter + vector(0, 0, GroundRadius);
		// Use direction from that point to the groundplane as the
		// new virtual direction
		Direction = normalize(GP-TP);
		
		// Smoothen out the joint a bit....
		// Thanks to Vlado for suggestion!
		if (Direction[2] > -0.1)
		{
			float fac = 1.0 - Direction[2] * -10.0;
			fac *= fac;
			
			Direction = mix(Direction, OrgDir, fac);
		}
	}
		} 
*/