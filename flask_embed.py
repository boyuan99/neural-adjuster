from threading import Thread

from flask import Flask, render_template
from tornado.ioloop import IOLoop

import numpy as np
from bokeh.embed import server_document
from bokeh.models import ColumnDataSource, Slider
from bokeh.plotting import figure
from bokeh.layouts import row, column
from bokeh.server.server import Server
from bokeh.themes import Theme

app = Flask(__name__)

params=dict(V_1=[30.0], V_2=[15.0], V_3=[0.0], V_4=[30.0],
            phi=[0.025], C=[6.698], dt=[1e-4],
            E_L=[-50.0], E_Ca=[100.0], E_K=[-70.0],
            g_L=[0.5], g_Ca=[1.1], g_K=[2.0])

def ml_step(I_syn, V, N, dt, params=params):
    dt = dt * 1e3
    V_1 = params['V_1'][0]
    V_2 = params['V_2'][0]
    V_3 = params['V_3'][0]
    V_4 = params['V_4'][0]
    phi = params['phi'][0]
    E_L = params['E_L'][0]
    E_Ca = params['E_Ca'][0]
    E_K = params['E_K'][0]

    g_L = params['g_L'][0]
    g_Ca = params['g_Ca'][0]
    g_K = params['g_K'][0]
    C = params['C'][0]

    dV = (I_syn - g_L * (V - E_L) - 0.5 * g_Ca * (1 + np.tanh((V - V_1) / V_2)) * (V - E_Ca) - g_K * N * (V - E_K)) / C
    dN = (0.5 * (1 + np.tanh((V - V_3) / V_4)) - N) * (phi * np.cosh((V - V_3) / (2 * V_4)))

    V1 = V + dV * dt
    N1 = N + dN * dt
    return [V1, N1]


def morris_bkapp(doc):
    params = dict(V_1=[30.0], V_2=[15.0], V_3=[0.0], V_4=[30.0],
                  phi=[0.025], C=[6.698], dt=[1e-4],
                  E_L=[-50.0], E_Ca=[100.0], E_K=[-70.0],
                  g_L=[0.5], g_Ca=[1.1], g_K=[2.0],
                  V_init=[-50.0], N_init=[0.02])

    params_source = ColumnDataSource(data=params)

    dt = 1e-4
    t = np.arange(0, 1, dt)

    I_syn = np.zeros_like(t)
    I_syn[2000:3000] = 1

    V = np.zeros_like(t)
    N = np.zeros_like(t)
    V[0] = params['V_init'][0]
    N[0] = params['N_init'][0]

    for i in range(len(t)):
        V_pre, N_pre = ml_step(I_syn[i], V[i], N[i], dt)
        if i < len(t) - 1:
            V[i + 1] = V_pre

    source = ColumnDataSource(data=dict(I=I_syn, V=V, t=t, N=N))

    plot1 = figure(width=600, height=300)
    # plot.line('t', 'I', source=source, line_color='orange', legend_label='I_syn')
    plot1.line('t', 'V', source=source, line_color='skyblue', line_width=3, legend_label='V')
    plot2 = figure(width=600, height=300)
    plot2.line('t', 'I', source=source, line_color='orange', line_width=3, legend_label='I_syn')

    slider_V_1 = Slider(start=-120.0, end=120.0, value=30.0, step=.5, title="V_1")
    slider_V_2 = Slider(start=-120.0, end=120.0, value=15.0, step=.5, title="V_2")
    slider_V_3 = Slider(start=-120.0, end=120.0, value=0.0, step=.5, title="V_3")
    slider_V_4 = Slider(start=-120.0, end=120.0, value=30.0, step=.5, title="V_4")
    slider_V_init = Slider(start=-120.0, end=120.0, value=-50.0, step=.5, title="V_init")
    slider_N_init = Slider(start=-5.0, end=5.0, value=0.02, step=.01, title="N_init")
    slider_E_L = Slider(start=-120.0, end=120.0, value=-50.0, step=.5, title="E_L")
    slider_E_K = Slider(start=-120.0, end=120.0, value=-70.0, step=.5, title="E_K")
    slider_E_Ca = Slider(start=-120.0, end=120.0, value=100.0, step=.5, title="E_Ca")
    slider_g_L = Slider(start=-10.0, end=10.0, value=0.5, step=.1, title="g_L")
    slider_g_K = Slider(start=-10.0, end=10.0, value=2.0, step=.1, title="g_K")
    slider_g_Ca = Slider(start=-10.0, end=10.0, value=1.1, step=.1, title="g_Ca")
    slider_phi = Slider(start=0, end=5, value=0.025, step=.025, title="phi")
    slider_C = Slider(start=0.0, end=10.0, value=6.0, step=.1, title="C")

    def update(attrname, old, new):
        V_1_update = slider_V_1.value
        V_2_update = slider_V_2.value
        V_3_update = slider_V_3.value
        V_4_update = slider_V_4.value
        E_L_update = slider_E_L.value
        E_K_update = slider_E_K.value
        E_Ca_update = slider_E_Ca.value
        g_L_update = slider_g_L.value
        g_K_update = slider_g_K.value
        g_Ca_update = slider_g_Ca.value
        phi_update = slider_phi.value
        C_update = slider_C.value
        V_init_update = slider_V_init.value
        N_init_update = slider_N_init.value

        params_update = dict(V_1=[V_1_update], V_2=[V_2_update], V_3=[V_3_update], V_4=[V_4_update],
                             phi=[phi_update], C=[C_update], dt=[1e-4],
                             E_L=[E_L_update], E_Ca=[E_Ca_update], E_K=[E_K_update],
                             g_L=[g_L_update], g_Ca=[g_Ca_update], g_K=[g_K_update],
                             V_init=[V_init_update], N_init=[N_init_update])

        V = np.zeros_like(t)
        N = np.zeros_like(t)
        V[0] = params_update['V_init'][0]
        N[0] = params_update['N_init'][0]
        for i in range(len(t)):
            V_pre, N_pre = ml_step(I_syn[i], V[i], N[i], dt, params_update)
            if i < len(t) - 1:
                V[i + 1] = V_pre

        source.data = dict(I=I_syn, V=V, t=t, N=N)
        params_source.data = params

    for w in [slider_V_1, slider_V_2, slider_V_3, slider_V_4,
              slider_E_L, slider_E_K, slider_E_Ca,
              slider_g_L, slider_g_K, slider_g_Ca,
              slider_phi, slider_C, slider_V_init, slider_N_init]:
        w.on_change('value_throttled', update)

    inputs = column(slider_V_1, slider_V_2, slider_V_3, slider_V_4,
                    slider_E_L, slider_E_K, slider_E_Ca,
                    slider_g_L, slider_g_K, slider_g_Ca,
                    slider_phi, slider_C, slider_V_init, slider_N_init)

    doc.add_root(row(inputs, column(plot2, plot1)))

    doc.theme = Theme(filename="theme.yaml")


@app.route('/', methods=['GET'])
def bkapp_page():
    script = server_document('http://localhost:5006/bkapp')
    return render_template("embed.html", script=script, template="Flask")


def bk_worker():
    # Can't pass num_procs > 1 in this configuration. If you need to run multiple
    # processes, see e.g. flask_gunicorn_embed.py
    server = Server({'/bkapp': morris_bkapp}, io_loop=IOLoop(), allow_websocket_origin=["127.0.0.1:8000"])
    server.start()
    server.io_loop.start()

Thread(target=bk_worker).start()

if __name__ == '__main__':
    app.run(port=8000)
