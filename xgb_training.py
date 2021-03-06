# -*- coding: utf-8 -*-
"""promoter_2d_training.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1aRxto52isUA9ZByujWdTsXZ855m_2p2q
"""

data_dir = 'dataset/'

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import glob
import os

df_data = pd.DataFrame()
df_labels = []

print('Reading positive data ...')
for fileName in glob.glob(os.path.join('promoter', '*.{}'.format('csv'))):
    df = pd.read_csv(fileName, header=None)
#     print('In processing: ', fileName)
    df_new = df.stack().to_frame().T
    df_data = df_data.append(df_new, ignore_index=True)
    df_labels.append(1)

print('Finish loading positive data')

np.shape(df_labels)

print('Reading negative data ...')
for fileName in glob.glob(os.path.join('non_promoter', '*.{}'.format('csv'))):
    df = pd.read_csv(fileName, header=None)
#     print('In processing: ', fileName)
    df_new = df.stack().to_frame().T
    df_data = df_data.append(df_new, ignore_index=True)
    df_labels.append(0)
    
print('Finish loading positive data')

X_trn_bert2D = df_data
y_trn_bert2D = df_labels

X_trn, y_trn = X_trn_bert2D, y_trn_bert2D

X_trn.head()


X_trn_et = pd.read_csv(os.path.join(data_dir, 'promoter.et.csv'), header=None)
X_trn_et.head()

corr_matrix = X_trn_et.corr(method='spearman').abs()

# Select upper triangle of correlation matrix
upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(np.bool))

# Find features with correlation greater than 0.8
to_get = [column for column in upper.columns if any(upper[column] > 0.8)]

# Drop features 
df_stat = X_trn_et[to_get]

df_stat.to_csv(os.path.join(data_dir, 'promoter.et.spearman.corr.sig.csv'), index=None)

from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from xgboost import XGBClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, confusion_matrix

kfold = StratifiedKFold(n_splits=5, shuffle=True)
from sklearn import metrics

def libsvm_model():
    clf = SVC(C=8, gamma=8, kernel='rbf', probability=True)
    return clf

def mlp_model():
    mlp = MLPClassifier()
    return mlp

def lr_model():
    knn = LogisticRegression()
    return knn

def randomforest_model():
    rf = RandomForestClassifier(max_features='auto', n_estimators=200, criterion='entropy', max_depth=7)
    return rf

def xgb_model():
    xgb = XGBClassifier(subsample=0.6, min_child_weight=1, max_depth=5, gamma=1.5, colsample_bytree=0.8)
    return xgb

def adaboost_model():
    ab = AdaBoostClassifier()
    return ab

def gaussian_model():
    gnb = GaussianNB()
    return gnb

def knn_model():
    knn = KNeighborsClassifier()
    return knn

X_et = pd.read_csv(os.path.join(data_dir, 'promoter.et.csv'), header=None)
X_et.head()

import matplotlib.pyplot as plt

from sklearn.metrics import roc_curve, auc
from sklearn.model_selection import train_test_split

y_trn = np.asarray(y_trn)

for train, test in kfold.split(X_et, y_trn):
#    train_x, train_y = X_trn.iloc[train], Y_trn.iloc[train]
    svm_model = xgb_model()   
    ## evaluate the model
    svm_model.fit(X_et.iloc[train], y_trn[train])
    # evaluate the model
    true_labels = np.asarray(y_trn[test])
    predictions = svm_model.predict(X_et.iloc[test])
    print(accuracy_score(true_labels, predictions))
    print(confusion_matrix(true_labels, predictions))
    pred_prob = svm_model.predict_proba(X_et.iloc[test])
    fpr, tpr, thresholds = metrics.roc_curve(true_labels, pred_prob[:,1], pos_label=1)
    print('AUC = ', metrics.auc(fpr, tpr))

"""## SHAP"""

import shap
import xgboost
# load JS visualization code to notebook
shap.initjs()

model = xgboost.train({"learning_rate": 0.01}, xgboost.DMatrix(X_trn_et, label=y_trn), 100)

# explain the model's predictions using SHAP
# (same syntax works for LightGBM, CatBoost, scikit-learn and spark models)
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_trn_et)

# summarize the effects of all the features
fig = plt.figure()
shap.summary_plot(shap_values, X_trn_et)
plt.show()

fig.savefig(os.path.join('fig', 'shap.effects.pdf'), dpi=300, bbox_inches='tight')
fig.savefig(os.path.join('fig', 'shap.effects.svg'), dpi=300, bbox_inches='tight')
fig.savefig(os.path.join('fig', 'shap.effects.png'), dpi=300, bbox_inches='tight')

df_shap = pd.DataFrame(data=shap_values, columns=X_trn_et.columns).abs()
df_shap.to_csv('results/shap.csv', index=None)

"""## RFE"""

df_feat_impt = pd.read_csv('results/shap_feat.csv')
df_feat_impt.head()

df_feat_impt.feature[0:2].values

X_trn_et[df_feat_impt.feature[0:2].values]

for x in range(1, 659):
    tmp = df_feat_impt.feature[0:x].values
    cv_score = []
    for train, test in kfold.split(X_trn_et[tmp], y_trn):
    #    train_x, train_y = X_trn.iloc[train], Y_trn.iloc[train]
        svm_model = xgb_model()   
        ## evaluate the model
        svm_model.fit(X_trn_et[tmp].iloc[train], y_trn[train])
        # evaluate the model
        true_labels = np.asarray(y_trn[test])
        predictions = svm_model.predict(X_trn_et[tmp].iloc[test])
        # print(accuracy_score(true_labels, predictions))
        # print(confusion_matrix(true_labels, predictions))
        cv_score.append(accuracy_score(true_labels, predictions))

    print('CV score: %s features: %s' % (x, np.mean(cv_score)))

"""### Train with SHAP features"""

X_trn_shap = X_trn_et[df_feat_impt.feature[0:659].values]
X_trn_shap.head()

X_trn_shap.to_csv(os.path.join(data_dir, 'promoter.shap.csv'), index=None, header=None)

final_cm = []
final_acc = 0
final_auc = 0
for x in range(0, 1):
    conf_matrices = np.zeros((2, 2))
    acc_cv_scores = []
    auc_cv_scores = []

    for train, test in kfold.split(X_trn_shap, y_trn):
    #    train_x, train_y = X_trn.iloc[train], Y_trn.iloc[train]
        svm_model = xgb_model()  
        ## evaluate the model
        svm_model.fit(X_trn_shap.iloc[train], y_trn[train])
        # evaluate the model
        true_labels = np.asarray(y_trn[test])
        predictions = svm_model.predict(X_trn_shap.iloc[test])
        conf_matrices = [[conf_matrices[i][j] + confusion_matrix(true_labels, predictions)[i][j]
                   for j in range(len(conf_matrices[0]))] for i in range(len(conf_matrices))]
        acc_cv_scores.append(accuracy_score(true_labels, predictions))
        # print(confusion_matrix(true_labels, predictions))
        pred_prob = svm_model.predict_proba(X_trn_shap.iloc[test])
        fpr, tpr, thresholds = metrics.roc_curve(true_labels, pred_prob[:,1], pos_label=1)
        auc_cv_scores.append(metrics.auc(fpr, tpr))
    
    if np.mean(acc_cv_scores) > final_acc:
        final_acc = np.mean(acc_cv_scores)
        final_cm = conf_matrices
        final_auc = np.mean(auc_cv_scores)
        print('Best accuracy of {} at loop {}'.format(np.mean(acc_cv_scores), x))

print('Accuracy = ', final_acc)
print('TP = {}, FP = {}, TN = {}, FN = {}'.format(final_cm[1][1], final_cm[0][1], final_cm[0][0], final_cm[1][0]))
print('AUC = ', final_auc)

"""## Other features"""

def load_data(fdata):
    df = pd.read_csv(os.path.join(data_dir, fdata), header=None)
    X = df.iloc[:,1:]
    y = df[0]
    return X, y

def load_strength_data(fdata):
    df = pd.read_csv(os.path.join(data_dir, fdata), header=None)
    X = df.iloc[0:3382,1:]
    y = df.iloc[0:3382,0]
    
    return X, y

X_trn_DAC, y_trn_DAC = load_data('promoter.DAC.csv')
X_trn_DCC, y_trn_DCC = load_data('promoter.DCC.csv')
X_trn_DACC, y_trn_DACC = load_data('promoter.DACC.csv')
X_trn_binary, y_trn_binary = load_data('promoter.binary.csv')
X_trn_CKSNAP, y_trn_CKSNAP = load_data('promoter.CKSNAP.csv')
X_trn_DNC, y_trn_DNC = load_data('promoter.DNC.csv')
X_trn_EIIP, y_trn_EIIP = load_data('promoter.EIIP.csv')
X_trn_ENAC, y_trn_ENAC = load_data('promoter.ENAC.csv')
X_trn_Kmer, y_trn_Kmer = load_data('promoter.Kmer.csv')
X_trn_NAC, y_trn_NAC = load_data('promoter.NAC.csv')
X_trn_NCP, y_trn_NCP = load_data('promoter.NCP.csv')
X_trn_PCPseDNC, y_trn_PCPseDNC = load_data('promoter.PCPseDNC.csv')
X_trn_PCPseTNC, y_trn_PCPseTNC = load_data('promoter.PCPseTNC.csv')
X_trn_PseDNC, y_trn_PseDNC = load_data('promoter.PseDNC.csv')
X_trn_PseEIIP, y_trn_PseEIIP = load_data('promoter.PseEIIP.csv')
X_trn_PseKNC, y_trn_PseKNC = load_data('promoter.PseKNC.csv')
X_trn_RCKmer, y_trn_RCKmer = load_data('promoter.RCKmer.csv')
X_trn_SCPseDNC, y_trn_SCPseDNC = load_data('promoter.SCPseDNC.csv')
X_trn_SCPseTNC, y_trn_SCPseTNC = load_data('promoter.SCPseTNC.csv')

# Load strength data
X_strength_bert, y_strength_bert = load_strength_data('promoter.strength.shap.csv')
# X_trn_DAC, y_trn_DAC = load_data('promoter.DAC.csv')
# X_trn_DCC, y_trn_DCC = load_data('promoter.DCC.csv')
# X_trn_DACC, y_trn_DACC = load_data('promoter.DACC.csv')
X_trn_binary, y_trn_binary = load_strength_data('promoter.binary.csv')
X_trn_CKSNAP, y_trn_CKSNAP = load_strength_data('promoter.CKSNAP.csv')
# X_trn_DNC, y_trn_DNC = load_data('promoter.DNC.csv')
X_trn_EIIP, y_trn_EIIP = load_strength_data('promoter.EIIP.csv')
X_trn_ENAC, y_trn_ENAC = load_strength_data('promoter.ENAC.csv')
X_trn_Kmer, y_trn_Kmer = load_strength_data('promoter.Kmer.csv')
# X_trn_NAC, y_trn_NAC = load_data('promoter.NAC.csv')
# X_trn_NCP, y_trn_NCP = load_data('promoter.NCP.csv')
# X_trn_PCPseDNC, y_trn_PCPseDNC = load_data('promoter.PCPseDNC.csv')
# X_trn_PCPseTNC, y_trn_PCPseTNC = load_data('promoter.PCPseTNC.csv')
X_trn_PseDNC, y_trn_PseDNC = load_strength_data('promoter.PseDNC.csv')
X_trn_PseEIIP, y_trn_PseEIIP = load_strength_data('promoter.PseEIIP.csv')
X_trn_PseKNC, y_trn_PseKNC = load_strength_data('promoter.PseKNC.csv')
X_trn_RCKmer, y_trn_RCKmer = load_strength_data('promoter.RCKmer.csv')
# X_trn_SCPseDNC, y_trn_SCPseDNC = load_data('promoter.SCPseDNC.csv')
# X_trn_SCPseTNC, y_trn_SCPseTNC = load_data('promoter.SCPseTNC.csv')

y_trn = y_strength_bert