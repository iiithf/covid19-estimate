#!/usr/bin/env python3
from scipy import optimize
from matplotlib import pyplot as plt
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import math


def csv_read(file):
  rows = pd.read_csv(file, comment='#')
  rows.drop(['Lat', 'Long', 'ISO 3166-1 Alpha 3-Codes', 'Region Code',
    'Sub-region Code', 'Intermediate Region Code'], axis=1, inplace=True)
  return rows


def filter_country(rows, country):
  is_country = rows['Country/Region'] == country
  return rows[is_country]


def merge_date(rows):
  a = rows.iloc[0:0]
  dates = sorted(set(rows['Date']))
  for d in dates:
    rd = rows[rows['Date'] == d]
    rv = rd.iloc[0:1].copy()
    rv['Value'] = rd['Value'].sum()
    a = a.append(rv)
  return a


def diff_value(rows):
  r, c = rows.shape
  v0, value = 0, rows.columns.get_loc('Value')
  for i in range(r):
    v1 = rows.iloc[i, value]
    rows.iloc[i, value] = v1 - v0
    v0 = v1
  return rows


def average_value(rows, window=7):
  r, c = rows.shape
  w, value = [0] * window, rows.columns.get_loc('Value')
  for i in range(r):
    v1 = rows.iloc[i, value]
    w.append(v1)
    w.pop(0)
    rows.iloc[i, value] = sum(w) / window
  return rows


def gaussian(xs, a, b, c):
  return a * np.exp(-((xs-b)**2)/(2*c*c))

def curve(xs, a, b, c, d, e, f):
  s0 = gaussian(xs, a, b, c)
  s1 = gaussian(xs, d, e, f)
  return s0 + s1

def main(xs, ys, fn, ps, country='', estimate=''):
  plt.figure(figsize=(6, 4))
  plt.scatter(xs, ys, label=country+' 2-week cases')
  zs = fn(xs, ps[0], ps[1], ps[2], ps[3], ps[4], ps[5])
  loss = np.sum((ys - zs) ** 2)
  loss_str = np.format_float_scientific(loss, unique=False, exp_digits=2,precision=3)
  xs = list(range(len(ys) * 2))
  zs = fn(xs, ps[0], ps[1], ps[2], ps[3], ps[4], ps[5])
  total = int(np.sum(np.clip(ys, 0, None)))
  print('Current total cases:', total)
  total = int(np.sum(np.clip(zs, 0, None)))
  print(estimate+' total cases:', total)
  plt.plot(xs, zs, label=estimate+', loss: '+loss_str)
  plt.legend(loc='best')
  plt.show()
  print()


country = 'US'
lowvalue = 10
start_date = datetime.strptime('2020-01-22', '%Y-%m-%d')
csvfile = 'time_series_covid19_confirmed_global_narrow.csv'
rows = csv_read(csvfile)
rows = filter_country(rows, country)
rows = merge_date(rows)
rows = diff_value(rows)
rows = average_value(rows, 14)
ys = list(rows['Value'])
xs = list(range(len(ys)))
ps = np.asarray([5000, 60, 2, 5000, 70, 2])

main(xs, ys, curve, ps, country, 'Initial')
ps, ps_cov = optimize.curve_fit(curve, xs, ys, p0=ps)
main(xs, ys, curve, ps, country, 'Estimate')
for x in range(len(xs), 10*len(xs)):
  v = curve([x], ps[0], ps[1], ps[2], ps[3], ps[4], ps[5])
  if v[0] < lowvalue:
    end_date = start_date + timedelta(days=x)
    print('low cases', int(v[0]), 'on', end_date)
    break
