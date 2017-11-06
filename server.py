from flask import Flask, render_template, request, jsonify
import numpy as np
from scipy.interpolate import interp1d
from scipy.integrate import quadrature

def prob_damage_states(damfun, poecurve):
    pds = {}
    for ds in damfun.ds:
        pgas, poes = zip(*poecurve)
        paddedpgas = [0] + list(pgas) + [3]
        paddedpoes = [1] + list(poes) + [0]
        poef = interp1d(paddedpgas, paddedpoes)
        kernel = lambda x: damfun(ds, x) * (1 - poef(x))
        pds[ds] = 1 - quadrature(kernel, 0, 3)[0]

    return pds

def lognormal_pdf(x , m, s):
    return np.exp( - ((np.log(x) - m)**2) / (2 * s**2) ) / ( x * np.sqrt(2 * np.pi) * s)


class DamageFunction(object):
    def __init__(self, damage_stetes):
        self.ds = damage_stetes.keys()
        self.params = {}
        self.statefuncs = {}
        for ds in self.ds:
            m, s = damage_stetes[ds]
            v = s**2
            mu = np.log((m**2)/np.sqrt(v+m**2));
            sigma = np.sqrt(np.log(v/(m**2)+1))
            self.params[ds] = (mu, sigma)
    def __call__(self, ds, im):
        return lognormal_pdf(im, *self.params[ds])

concrete_vals = {"light damage": (0.15, 0.08),
                "significant damage": (0.27, 0.15),
                "collapse": (0.33, 0.17)}

concrete_df = DamageFunction(concrete_vals)

damage_functions_vals = {
        "concrete low rise":concrete_vals,
        "concrete high rise":concrete_vals,
        "masonry low rise":concrete_vals,
        "masonry high rise":concrete_vals,
    }

dfs = {}
for df in damage_functions_vals:
    dfs[df] = DamageFunction(damage_functions_vals[df])



if __name__ == "__main__":

    app = Flask(__name__)

    pgas = [0.0009, 0.001, 0.002, 0.003, 0.004, 0.005, 0.007, 0.0098,
        0.0137, 0.0192, 0.0269, 0.0376, 0.0527, 0.0738, 0.103, 0.145,
        0.203, 0.284, 0.397, 0.556, 0.778, 1.09]
    poes = [1.000000E+00,1.000000E+00,1.000000E+00,9.999999E-01,9.999986E-01,
    9.999846E-01,9.996885E-01,9.965282E-01,9.779567E-01,9.135878E-01,7.752770E-01,
    5.804895E-01,3.827021E-01,2.282403E-01,1.266045E-01,6.451745E-02,3.096786E-02,
    1.373655E-02,5.548974E-03,1.985997E-03,6.205522E-04,1.643732E-04]

    @app.route("/")
    def simple_answer():
        return app.send_static_file('frontpage.html')

    @app.route("/hazard", methods=["GET", "POST"])
    def get_hazard_curve():
        latitude = request.args.get("lat")
        latitude = request.args.get("lon")
        app.logger.debug(latitude)
        app.logger.debug(request.args)
        # query ----> poes, pgas 
        ers = [-np.log(1-poe)/50. if poe < 1 else "Infinity" for poe in poes]
        rps = [1./er  if er != "Infinity" else 0 for er in ers]
        pga_50y = interp1d(rps, pgas)
        val = pga_50y(50).tolist()
        val = 0.6
        data = {"pga":pgas, "poe":poes, "er":ers, "rp":rps, "pga50y":val}
        app.logger.debug(data)

        return jsonify(data)

    @app.route("/risk")
    def get_risk():
        latitude = request.args.get("lat")
        latitude = request.args.get("lon")
        exposure = request.args.get("exposure")
        app.logger.debug(request.args)
        ds = prob_damage_states(dfs[exposure], zip(pgas, poes))
        data = {"ds":ds}
        return jsonify(data)

    @app.route("/damfun")
    def get_dfs():
        data = sorted(damage_functions_vals.keys())
        app.logger.debug(data)
        return jsonify(data)

    app.debug = True
    app.run()
