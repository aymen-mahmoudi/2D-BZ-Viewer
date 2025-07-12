#!/usr/bin/env python

##############################################################################
##
# This file is part of 2D-BZ Viewer project.
##
# 2D-BZ Viewer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
##
##############################################################################

__author__ = ["Aymen Mahmoudi"]
__license__ = "GPL"
__date__ = "10/07/2025"

from PyQt5.QtWidgets import *
from PyQt5.uic import loadUiType
from PyQt5 import QtGui, QtCore
import numpy as np
import pandas as pd
import sys

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from scipy.spatial import Voronoi

from gui import Ui_Form as ui  # from gui.py

class MainWindow(QWidget, ui):
    def __init__(self):
        QWidget.__init__(self)
        self.setupUi(self)
        self.plot_layout()
        self.HandleButtons()

    def HandleButtons(self):
        self.update_pushButton.clicked.connect(self.essential_values)
        self.update_pushButton.clicked.connect(self.plot)

    def plot_layout(self):
        self.fig = plt.figure(facecolor='w')
        self.canvas = FigureCanvas(self.fig)
        toolbar = NavigationToolbar(self.canvas, self)
        self.plottingSpace_verticallayout.addWidget(toolbar)
        self.plottingSpace_verticallayout.addWidget(self.canvas)

    def compute_2d_lattice(self, a, b, gamma_deg):
        gamma = np.radians(gamma_deg)
        a1 = np.array([a, 0])
        a2 = np.array([b * np.cos(gamma), b * np.sin(gamma)])
        area = a1[0] * a2[1] - a1[1] * a2[0]
        if np.isclose(area, 0):
            raise ValueError("Lattice vectors are colinear or invalid: area = 0")
        b1 = 2 * np.pi * np.array([ a2[1], -a2[0]]) / area
        b2 = 2 * np.pi * np.array([-a1[1],  a1[0]]) / area
        return a1, a2, b1, b2, area

    def plot(self):
        self.fig.clear()
        ax1 = self.fig.add_subplot(121)
        ax2 = self.fig.add_subplot(122)

        a1, a2, b1, b2, area = self.compute_2d_lattice(
            self.a, self.b, self.gamma
        )

        points = []
        grid_range = 4
        for i in range(-grid_range, grid_range + 1):
            for j in range(-grid_range, grid_range + 1):
                r = i * a1 + j * a2
                points.append(r)
        points = np.array(points)
        ax1.plot(points[:, 0], points[:, 1], 'ko')
        ax1.quiver(0, 0, *a1, angles='xy', scale_units='xy', scale=1, color='r', linewidth=2)
        ax1.quiver(0, 0, *a2, angles='xy', scale_units='xy', scale=1, color='g', linewidth=2)
        ax1.set_aspect('equal')
        ax1.set_title("Real-space")
        ax1.set_xlabel('$x$'+' '+'$ (\AA)$', fontsize=10)
        ax1.set_ylabel('$y$'+' '+'$ (\AA)$', fontsize=10)
        ax1.grid(True, which='both', linestyle='--', alpha=0.5)
        ax1.minorticks_on()

        kpoints = []
        for i in range(-grid_range, grid_range + 1):
            for j in range(-grid_range, grid_range + 1):
                k = i * b1 + j * b2
                kpoints.append(k)
        kpoints = np.array(kpoints)

        vor = Voronoi(kpoints)
        origin_index = np.argmin(np.sum(kpoints ** 2, axis=1))
        bz_vertices = vor.regions[vor.point_region[origin_index]]
        bz = np.array([vor.vertices[i] for i in bz_vertices if i != -1])

        Gamma = np.array([0, 0])
        def angle_from_gamma(v): return np.arctan2(v[1] - Gamma[1], v[0] - Gamma[0])
        bz_sorted = sorted(bz, key=angle_from_gamma)
        bz_sorted = np.array(bz_sorted)

        ax2.plot(kpoints[:, 0], kpoints[:, 1], 'ko', markersize=2, alpha=0.2)
        ax2.fill(bz_sorted[:, 0], bz_sorted[:, 1], edgecolor='navy', fill=False, linewidth=2.5)

        Y = 0.5 * (bz_sorted[0] + bz_sorted[1])
        B = 0.5 * (bz_sorted[1] + bz_sorted[2])
        A = bz_sorted[2]

        ax2.plot(*Gamma, 'ro')
        ax2.text(*Gamma, r' $\Gamma$', fontsize=13, color='red')
        ax2.plot(*Y, 'go')
        ax2.text(*Y, ' Y', fontsize=12, color='green')
        ax2.plot(*B, 'mo')
        ax2.text(*B, ' B', fontsize=12, color='magenta')
        ax2.plot(*A, 'co')
        ax2.text(*A, ' A', fontsize=12, color='cyan')

        ax2.quiver(0, 0, *b1, angles='xy', scale_units='xy', scale=1, color='orange', linewidth=2, label='b₁')
        ax2.quiver(0, 0, *b2, angles='xy', scale_units='xy', scale=1, color='purple', linewidth=2, label='b₂')

        b1_len = np.linalg.norm(b1)
        b2_len = np.linalg.norm(b2)
        ax2.text(0.05, 0.95, f"|b₁| = {b1_len:.2f} Å⁻¹", transform=ax2.transAxes, fontsize=10, verticalalignment='top')
        ax2.text(0.05, 0.90, f"|b₂| = {b2_len:.2f} Å⁻¹", transform=ax2.transAxes, fontsize=10, verticalalignment='top')

        ax2.set_aspect('equal')
        ax2.set_title("k-space", fontsize=14)
        ax2.set_xlabel('$k_{x}$'+' '+'$ (\AA^{-1})$', fontsize=10)
        ax2.set_ylabel('$k_{y}$'+' '+'$ (\AA^{-1})$', fontsize=10)

        ax2.grid(True, which='both', linestyle='--', alpha=0.5)
        ax2.minorticks_on()
        ax2.legend()

        dist_GY = np.linalg.norm(Y - Gamma)
        dist_GB = np.linalg.norm(B - Gamma)
        dist_GA = np.linalg.norm(A - Gamma)

        self.gammaY_lineEdit.setText(f"{dist_GY:.2f}")
        self.gammaB_lineEdit.setText(f"{dist_GB:.2f}")
        self.gammaA_lineEdit.setText(f"{dist_GA:.2f}")

        self.fig.tight_layout()

        self.canvas.draw()

    def essential_values(self):
        self.a = float(self.get_a())
        self.b = float(self.get_b())
        self.gamma = float(self.get_gamma())

    def get_a(self):
        return self.a_lineEdit.text()

    def get_b(self):
        return self.b_lineEdit.text()

    def get_gamma(self):
        return self.gamma_lineEdit.text()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()

if __name__ == "__main__":
    main()
