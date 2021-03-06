#!/usr/bin/env python
# coding: utf-8

import os
import pandas as pd
from sklearn.metrics import roc_auc_score

def main():
    rawfile_dir = '../input/'
    dataset_dir = '../processed/dataset/'
    model_output_dir = f'../processed/lgb_output/'
    submitfile_dir = '../output/'
    if not os.path.isdir(submitfile_dir):
        os.makedirs(submitfile_dir)

    y_train = pd.read_pickle(os.path.join(dataset_dir, 'y_train.pickle'))
    real_id = pd.read_pickle(os.path.join(dataset_dir, 'real_id.pickle'))
    fake_id = pd.read_pickle(os.path.join(dataset_dir, 'fake_id.pickle'))

    oof_pred_list = []
    test_pred_list = []
    for fold_set_number in range(10):
        _oof_pred = pd.read_pickle(os.path.join(model_output_dir, f'oof_preds_{fold_set_number}.pkl.gz'))\
            .rank(pct=True).reset_index()
        for model_management_num in range(fold_set_number, fold_set_number+5):
            _test_pred = pd.read_pickle(os.path.join(model_output_dir, f'test_preds_{model_management_num}.pkl.gz'))
            _real_test_pred = _test_pred.loc[real_id]
            _fake_test_pred = _test_pred.loc[fake_id]
            _real_test_pred = _real_test_pred.rank(pct=True).reset_index()
            _fake_test_pred = _fake_test_pred.rank(pct=True).reset_index()
            test_pred_list.append(pd.concat([_real_test_pred, _fake_test_pred], axis=0))
        _auc = roc_auc_score(y_train.loc[_oof_pred['ID_code']], _oof_pred[f'pred'])
        print('{0} : {1:.6f}'.format(fold_set_number, _auc))
        oof_pred_list.append(_oof_pred)
    oof_pred_concat_rank = pd.concat(oof_pred_list, axis=0)
    test_pred_concat_rank = pd.concat(test_pred_list, axis=0)
    oof_pred_rank_mean = oof_pred_concat_rank.groupby('ID_code').mean()
    test_pred_rank_mean = test_pred_concat_rank.groupby('ID_code').mean()
    total_auc = roc_auc_score(y_train.loc[oof_pred_rank_mean.index], oof_pred_rank_mean)
    print('total mean auc : {0:.6f}'.format(total_auc))

    sub = pd.read_csv(os.path.join(rawfile_dir, 'sample_submission.csv.zip'))
    sub = sub[['ID_code']].merge(
        test_pred_rank_mean.reset_index().rename(columns={'pred':'target'}), how='left').fillna(0)
    sub.to_csv(os.path.join(submitfile_dir, 'akiyama_lgb.csv.gz'), index=False, compression='gzip')

if __name__ == '__main__':
    main()
