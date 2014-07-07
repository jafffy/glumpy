#! /usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2014, Nicolas P. Rougier. All Rights Reserved.
# Distributed under the (new) BSD License.
# -----------------------------------------------------------------------------
import numpy as np
import glumpy.gl as gl
import glumpy.app as app
import glumpy.glm as glm
import glumpy.gloo as gloo

vertex = """
    attribute vec2 a_texcoord;
    attribute vec2 a_position;
    varying vec2 v_texcoord;
    void main()
    {
        gl_Position = vec4(a_position, 0.0, 1.0);
        v_texcoord = a_texcoord;
    } """

fragment = """
    float
    compute_alpha(float d, float width, float antialias)
    {
        d -= width/2.0 - antialias;
        if( d < 0.0 )
        {
            return 1.0;
        }
        else
        {
            float alpha = d/antialias;
            return exp(-alpha*alpha);
        }
    }

    uniform vec2      u_size;
    uniform vec2      u_translate;
    uniform float     u_scale;
    uniform float     u_antialias;

    uniform float     u_major_grid_width;
    uniform float     u_minor_grid_width;
    uniform vec4      u_major_grid_color;
    uniform vec4      u_minor_grid_color;
    uniform vec2      u_major_tick_size;
    uniform vec2      u_minor_tick_size;
    uniform float     u_major_tick_width;
    uniform float     u_minor_tick_width;
    uniform vec4      u_major_tick_color;
    uniform vec4      u_minor_tick_color;
    uniform sampler2D u_grid;

    varying vec2 v_texcoord;
    void main()
    {
        float x = v_texcoord.x * u_size.x; // - u_translate.x;
        float y = v_texcoord.y * u_size.y; // - u_translate.y;

        vec4 Tx = texture2D(u_grid, vec2(v_texcoord.x,0.5));
        float Mx = abs(x - Tx.x - 0.315);
        float mx = abs(x - Tx.z - 0.315);

        vec4 Ty = texture2D(u_grid, vec2(v_texcoord.y,0.5));
        float My = abs(y - Ty.y - 0.315);
        float my = abs(y - Ty.w - 0.315);

        // Major grid
        float M = min(Mx,My);

        // Minor grid
        float m = min(mx,my);

        vec4 color = u_major_grid_color;
        float alpha1 = compute_alpha( M, u_major_grid_width, u_antialias);
        float alpha2 = compute_alpha( m, u_minor_grid_width, u_antialias);
        float alpha  = alpha1;
        if( alpha2 > alpha1*1.5 )
        {
            alpha = alpha2;
            color = u_minor_grid_color;
        }

        // Top major ticks
        if( y > (u_size.y - u_major_tick_size.y) )
        {
            float a = compute_alpha(Mx, u_major_tick_width, u_antialias);
            if (a > alpha)
            {
               alpha = a;
               color = u_major_tick_color;
            }
        }

        // Bottom major ticks
        else if( y < u_major_tick_size.y )
        {
            float a = compute_alpha(Mx, u_major_tick_width, u_antialias);
            if (a > alpha)
            {
               alpha = a;
               color = u_major_tick_color;
            }
        }

        // Left major ticks
        if( x < u_major_tick_size.x )
        {
            float a = compute_alpha(My, u_major_tick_width, u_antialias);
            if (a > alpha )
            {
               alpha = a;
               color = u_major_tick_color;
            }
        }

        // Right major ticks
        else if( x > (u_size.x - u_major_tick_size.x) )
        {
            float a = compute_alpha(My, u_major_tick_width, u_antialias);
            if (a > alpha )
            {
               alpha = a;
               color = u_major_tick_color;
            }
        }

        // Top minor ticks
        if( y > (u_size.y - u_minor_tick_size.y) )
        {
            float a = compute_alpha(mx, u_minor_tick_width, u_antialias);
            if (a > alpha)
            {
               alpha = a;
               color = u_minor_tick_color;
            }
        }

        // Bottom minor ticks
        else if( y < u_minor_tick_size.y )
        {
            float a = compute_alpha(mx, u_minor_tick_width, u_antialias);
            if (a > alpha)
            {
               alpha = a;
               color = u_minor_tick_color;
            }
        }

        // Left minor ticks
        if( x < u_minor_tick_size.x )
        {
            float a = compute_alpha(my, u_minor_tick_width, u_antialias);
            if (a > alpha )
            {
               alpha = a;
               color = u_minor_tick_color;
            }
        }

        // Right major ticks
        else if( x > (u_size.x - u_minor_tick_size.x) )
        {
            float a = compute_alpha(my, u_minor_tick_width, u_antialias);
            if (a > alpha )
            {
               alpha = a;
               color = u_minor_tick_color;
            }
        }

        gl_FragColor = vec4(color.xyz, alpha*color.a);
    }
    """


def find_closest(A, target):
    # A must be sorted
    idx = A.searchsorted(target)
    idx = np.clip(idx, 1, len(A) - 1)
    left = A[idx - 1]
    right = A[idx]
    idx -= target - left < right - target
    return idx


def update_grid(w, h):

    n = Z.shape[1]

    # Logarithmic grid
    t1 = major_grid[0] * scale
    t2 = minor_grid[0] * scale
    t3 = major_grid[1] * scale
    t4 = minor_grid[1] * scale

    L = (np.log(np.linspace(1,10,10,endpoint=True))-np.log(1))/np.log(10)
    L = (L[+1:-1])

    I1 = np.arange( np.fmod(translate[0], t1), np.fmod(translate[0], t1) + w + t1, t1)
    I2 = np.repeat(I1,8).reshape(len(I1),8)
    I2[:] += L * t1
    I2 = I2.ravel()

    I3 = np.arange( np.fmod(translate[1], t3), np.fmod(translate[1], t3) + h + t3, t3)
    I4 = np.repeat(I3,8).reshape(len(I3),8)
    # I4[:] += (np.log(np.arange(1,11))/np.log(10)) * t1
    I4[:] += L * t3
    I4 = I4.ravel()

    # Logarithmic grid
    # (np.log(np.arange(1,11))/np.log(10))[1:-1]
#    I1 = np.logspace(np.log10(1), np.log10(2 * w), 5) * scale
#    I2 = np.logspace(np.log10(1), np.log10(2 * w), 50) * scale
#    I3 = np.logspace(np.log10(1), np.log10(2 * h), 5) * scale
#    I4 = np.logspace(np.log10(1), np.log10(2 * h), 50) * scale

    # We are here in screen space and we want integer coordinates
    np.floor(I1, out=I1)
    np.floor(I2, out=I2)
    np.floor(I3, out=I3)
    np.floor(I4, out=I4)

    L = np.linspace(0, w, n)
    Z[..., 0] = I1[find_closest(I1, L)]
    Z[..., 2] = I2[find_closest(I2, L)]
    L = np.linspace(0, h, n)
    Z[..., 1] = I3[find_closest(I3, L)]
    Z[..., 3] = I4[find_closest(I4, L)]

    program['u_grid'][...] = Z
    program['u_size'] = w, h


window = app.Window(width=2*512, height=2*512)

@window.event
def on_draw():
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    program.draw(gl.GL_TRIANGLE_STRIP)

@window.event
def on_resize(width, height):
    gl.glViewport(0, 0, width, height)
    update_grid(width, height)

@window.event
def on_mouse_drag(x, y, dx, dy, button):
    global translate, scale
    _, _, w, h = gl.glGetIntegerv(gl.GL_VIEWPORT)
    translate = [translate[0] + dx, translate[1] - dy]
    program['u_translate'] = translate
    update_grid(w, h)

@window.event
def on_mouse_scroll(x, y, dx, dy):
    global translate, scale
    _, _, w, h = gl.glGetIntegerv(gl.GL_VIEWPORT)
    y = h-y

    s = min(max(0.25, scale + .01 * dy * scale), 200)
    translate[0] = x - s * (x - translate[0]) / scale
    translate[1] = y - s * (y - translate[1]) / scale
    translate = [translate[0], translate[1]]
    scale = s
    program['u_translate'] = translate
    program['u_scale'] = scale
    update_grid(w, h)


program = gloo.Program(vertex, fragment, 4)
program['a_position'] = np.array([(-1, -1), (-1, +1), (+1, -1), (+1, +1)])
program['a_texcoord'] = (0, 0), (0, +1), (+1, 0), (+1, +1)
program['u_major_grid_width'] = 1.0
program['u_minor_grid_width'] = 1.0
program['u_major_grid_color'] = 0, 0, 0, .75
program['u_minor_grid_color'] = 0, 0, 0, .25
program['u_major_tick_size'] = 10, 10
program['u_minor_tick_size'] = 5, 5
program['u_major_tick_width'] = 2.0
program['u_minor_tick_width'] = 1.1
program['u_major_tick_color'] = 0, 0, 0, 1
program['u_minor_tick_color'] = 0, 0, 0, 1
program['u_antialias'] = 1.0
program['u_translate'] = 0, 0
program['u_scale'] = 1.0
program['u_size'] = 512.0, 512.0
major_grid = np.array([64, 64])
minor_grid = np.array([8, 8])
Z = np.zeros((1, 2 * 1024, 4), dtype=np.float32)
program['u_grid'] = Z
program['u_grid'].interpolation = gl.GL_NEAREST
translate = [0, 0]
scale = 1

gl.glClearColor(1, 1, 1, 1)
gl.glEnable(gl.GL_BLEND)
gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

app.run()