#version 330 core
#ifdef GL_ES
   precision highp float;
#endif

#define PI 3.14159265359

uniform sampler2D tex;
uniform vec2 curvature;
uniform vec2 screenResolution;
uniform vec2 scanLineOpacity;
uniform float vignetteOpacity;
uniform float brightness;
uniform float bigScanLineOpacity;
uniform float vignetteRoundness;
uniform float time;

in vec2 uv;
out vec4 f_color;

vec4 scanLineIntensity(float uv_, float resolution, float opacity)
{
    float intensity = sin(uv_ * resolution * PI * 2.0);
    intensity = ((0.5 * intensity) + 0.5) * 0.9 + 0.1;
    return vec4(vec3(pow(intensity, opacity)), 1.0);
}

vec4 bigScanLineIntensity(float uv_, float opacity)
{
    float intensity = sin(((uv_ * 2) * PI * 2.0) + 0.02 * time);
    intensity = (intensity + 3)*0.25;
    return vec4(vec3(intensity * (1 - opacity)), 1.0);
}

vec2 curveRemapUV(vec2 uv_) {
    // as we near the edge of our screen apply greater distortion using a cubic function
    uv_ = uv_ * 2.0-1.0;
    vec2 offset = abs(uv_.yx) / vec2(curvature.x, curvature.y);
    uv_ = uv_ + uv_ * offset * offset;
    uv_ = uv_ * 0.5 + 0.5;
    return uv_;
}

vec4 vignetteIntensity(vec2 uv_, vec2 resolution, float opacity, float roundness)
{
    float intensity = uv_.x * uv_.y * (1.0 - uv_.x) * (1.0 - uv_.y);
    return vec4(vec3(clamp(pow((resolution.x / roundness) * intensity, opacity), 0.0, 1.0)), 1.0);
}

void main() {
    vec2 remappedUV = curveRemapUV(vec2(uv.x, uv.y));
    vec4 baseColor = vec4(texture(tex, remappedUV).rgb, 1.0);

    //scan lines
    baseColor *= scanLineIntensity(remappedUV.x, screenResolution.y, scanLineOpacity.x);
    baseColor *= scanLineIntensity(remappedUV.y, screenResolution.x, scanLineOpacity.y);
    baseColor *= bigScanLineIntensity(uv.y, bigScanLineOpacity);

    baseColor *= vignetteIntensity(remappedUV, screenResolution, vignetteOpacity, vignetteRoundness);

    baseColor *= vec4(vec3(brightness), 1.0);

    //baseColor *= vec4(vec3(brightness), 1.0);

    if (remappedUV.x < 0.0 || remappedUV.y < 0.0 || remappedUV.x > 1.0 || remappedUV.y > 1.0) {
        f_color = vec4(0.0, 0.0, 0.0, 1.0);
    } else {
        f_color = baseColor;
    }
}