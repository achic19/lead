import pickle

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import ShuffleSplit
from sklearn.model_selection import cross_validate

if __name__ == '__main__':
    algorithm_dictionary = {'random forest': RandomForestClassifier()}
    # Upload and prepare  data
    columns = ['highway', 'choice', 'integ', 'amenity', 'office', 'tourism', 'shop', 'building', 'natural',
               'leisure', 'landuse', 'time', 'day', 'ped_flow', 'location', 'date', 'length']
    df = pd.read_csv('small_date_to_ml.csv')

    X = df.loc[:, columns[0:13]].to_numpy()
    y = df.loc[:, columns[13]].to_numpy()
    res_list = []
    # Initial MLPClassifier
    for clf in algorithm_dictionary.items():
        # # specify parameters and distributions to sample from
        # # Cross validation
        print(clf[0])

        cv = ShuffleSplit(n_splits=20, test_size=0.3, random_state=0)

        scoring = ['accuracy', 'f1_micro']

        scores = cross_validate(clf[1], X, y, cv=cv, scoring=scoring, n_jobs=-1, return_estimator=True)
        mean = scores['test_accuracy'].mean()
        std = scores['test_accuracy'].std()
        print("Accuracy :%0.3f (+/- %0.4f)" % (mean, std))
        # print("test_f1 : %0.3f (+/- %0.4f)" % (scores['test_f1'].mean(), scores['test_f1'].std()))
        print("test_f1_micr : %0.3f (+/- %0.4f)" % (scores['test_f1_micro'].mean(), scores['test_f1_micro'].std()))
        # print("test_precision : %0.3f (+/- %0.4f)" % (
        #     scores['test_precision'].mean(), scores['test_precision'].std()))
        # print("test_recall : %0.3f (+/- %0.4f)" % (scores['test_recall'].mean(), scores['test_recall'].std()))

        res_list.append(
            [clf[0], mean, std, scores['test_f1_micro'].mean(), scores['test_f1_micro'].std()])

        df = pd.DataFrame(res_list,
                          columns=['name', 'accuracy', 'accuracy_std', 'f1', 'f1_std'])

        df.to_csv('matrices.csv')
        # save the model with the highest score
        filename = 'finalized_model.sav'
        #  get more statistic about the best model -highest accuracy and feature importances
        best_results = np.argmax(scores['test_accuracy'])
        feature_importances = scores['estimator'][best_results].feature_importances_
        feature_importances = (feature_importances * 100).astype(int)
        # save the feature_importances as file
        with open('feature_importances.txt', 'w') as filehandle:
            for listitem in list(zip(columns[0:13], feature_importances)):
                filehandle.write('%s\n' % str(listitem))
        # save the model as a file
        print(scores['test_accuracy'][best_results])
        pickle.dump(scores['estimator'][best_results], open(filename, 'wb'))
