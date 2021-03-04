import os

os.environ["PATH"] += os.pathsep + r'C:\Program Files\graphviz-2.38\release/bin/'

import pandas as pd
# Model (can also use single decision tree)
from sklearn.ensemble import RandomForestClassifier
import pickle

if __name__ == '__main__':
    # Upload and prepare  data
    df = pd.read_csv('csv_files/results.csv')
    X = df.loc[:, df.columns[1:14]].to_numpy()
    y = df.loc[:, df.columns[14]].to_numpy()

    # Train
    model = RandomForestClassifier(n_estimators=97).fit(X, y)
    # save the model to disk
    filename = 'finalized_model.sav'
    pickle.dump(model, open(filename, 'wb'))

    # Extract single tree
    estimator = model.estimators_[96]

    from sklearn.tree import export_graphviz

    # Export as dot file
    export_graphviz(estimator, out_file='ped_flow.dot',
                    feature_names=df.columns[1:14].values,
                    class_names=["not optimal", "optimal"],
                    rounded=True, proportion=False,
                    precision=2, filled=True)

    # Convert to png using system command (requires Graphviz)
    # Convert a .dot file to .png
    from subprocess import call

    call(['dot', '-Tpdf', 'ped_flow.dot', '-o', 'ped_flow.pdf'])
    # from graphviz import render '-Gdpi=1500'
    # render('dot', 'png', 'tree.dot','-Gdpi=600')
