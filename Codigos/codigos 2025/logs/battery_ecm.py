import numpy as np
from scipy.optimize import curve_fit
import time

class BatteryEcm:
    """
    Equivalent circuit model (ECM) for battery parameter identification.
    """
    def __init__(self, data, params):
        self.current = data.current
        self.time = data.time
        self.voltage = data.voltage
        self.idd = data.get_indices_discharge()

        self.eta_chg = params['eta_chg']
        self.eta_dis = params['eta_dis']
        self.q_cell = params['q_cell']

    @staticmethod
    def func_otc(t, a, b, alpha):
        return a - b * np.exp(-alpha * t)

    @staticmethod
    def func_ttc(t, a, b, c, alpha, beta):
        return a - b * np.exp(-alpha * t) - c * np.exp(-beta * t)
    
    def get_rtau(self, rctau, z):
        soc = np.arange(0.1, 1.0, 0.1)[::-1]
        idx = abs(soc - z).argmin()
        tau1 = rctau[:, 0][idx]
        tau2 = rctau[:, 1][idx]
        r0 = rctau[:, 2][idx]
        r1 = rctau[:, 3][idx]
        r2 = rctau[:, 4][idx]
        return tau1, tau2, r0, r1, r2

    def soc(self):
        current, time, dt = self.current, self.time, np.diff(self.time)
        q = self.q_cell * 3600
        z = np.ones(len(current))
        for k in range(1, len(current)):
            eta = self.eta_chg if current[k] > 0 else self.eta_dis
            z[k] = z[k - 1] + (eta * current[k] * dt[k - 1] / q)
        return z

    def ocv(self, soc, pts=False, vz_pts=None):
        if pts is True:
            id0 = self.idd[0]
            v_pts = np.append(self.voltage[id0], self.voltage[-1])
            z_pts = np.append(soc[id0], soc[-1])
            i_pts = np.append(self.current[id0], self.current[-1])
            t_pts = np.append(self.time[id0], self.time[-1])
            ocv = np.interp(soc, z_pts[::-1], v_pts[::-1])
            return ocv, i_pts, t_pts, v_pts, z_pts
        elif vz_pts is not None:
            v_pts, z_pts = vz_pts
            ocv = np.interp(soc, z_pts[::-1], v_pts[::-1])
            return ocv
        else:
            id0 = self.idd[0]
            v_pts = np.append(self.voltage[id0], self.voltage[-1])
            z_pts = np.append(soc[id0], soc[-1])
            ocv = np.interp(soc, z_pts[::-1], v_pts[::-1])
            return ocv

    def curve_fit_coeff(self, func, ncoeff):
        _, _, id2, _, id4 = self.idd
        id2 = id2[:-1]
        nrow = len(id2)
        coeff = np.zeros((nrow, ncoeff))
        for i in range(nrow):
            start = id2[i]
            end = id4[i]
            t = self.time[start:end + 1]
            t_curve = t - t[0]
            v_curve = self.voltage[start:end + 1]
            if ncoeff == 3:
                guess = v_curve[-1], 0.0644, 0.0012
            elif ncoeff == 5:
                guess = v_curve[-1], 0.0724, 0.0575, 0.0223, 0.0007
            popt, pcov = curve_fit(func, t_curve, v_curve, p0=guess, maxfev=3000)
            coeff[i] = popt

        return coeff
    
    def rctau_ttc(self, coeff):
        id0, id1, id2, _, _, = self.idd
        id0 = np.delete(id0, -1)    # indices must be same length as `coeff`
        id1 = np.delete(id1, -1)
        id2 = np.delete(id2, -1)

        nrow = len(id0)
        rctau = np.zeros((nrow, 7))

        for k in range(nrow):
            di = abs(self.current[id1[k]] - self.current[id0[k]])
            dt = self.time[id2[k]] - self.time[id0[k]]
            dv = abs(self.voltage[id1[k]] - self.voltage[id0[k]])

            _, b, c, alpha, beta = coeff[k]

            tau1 = 1 / alpha
            tau2 = 1 / beta
            r0 = dv / di
            r1 = b / ((1 - np.exp(-dt / tau1)) * di)
            r2 = c / ((1 - np.exp(-dt / tau2)) * di)
            c1 = tau1 / r1
            c2 = tau2 / r2

            rctau[k] = tau1, tau2, r0, r1, r2, c1, c2

        return rctau

    def vt(self, soc, ocv, rctau):
        dt = np.diff(self.time)     # length of each time step, dt is not constant
        nc = len(self.current)      # total number of time steps based on current
        v0 = np.zeros(nc)           # initialize v0 array
        v1 = np.zeros(nc)           # initialize v1 array
        v2 = np.zeros(nc)           # initialize v2 array

        for k in range(1, nc):
            i = self.current[k]

            # get parameters at state of charge
            tau1, tau2, r0, r1, r2 = self.get_rtau(rctau, soc[k])

            # voltage in r0 resistor
            v0[k] = r0 * i

            # voltage in c1 capacitor
            tm1 = v1[k - 1] * np.exp(-dt[k - 1] / tau1)
            tm2 = r1 * (1 - np.exp(-dt[k - 1] / tau1)) * i
            v1[k] = tm1 + tm2

            # voltage in c2 capacitor
            tm3 = v2[k - 1] * np.exp(-dt[k - 1] / tau2)
            tm4 = r2 * (1 - np.exp(-dt[k - 1] / tau2)) * i
            v2[k] = tm3 + tm4

        vt = ocv + v0 + v1 + v2
        return vt        
 
