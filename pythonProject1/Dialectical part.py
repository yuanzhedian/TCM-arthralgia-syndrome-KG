import pandas as pd
from py2neo import Graph, Node, Relationship
import numpy as np
from sklearn.metrics import recall_score, precision_score, f1_score
import math


graph = Graph("bolt://localhost:7687", auth=("neo4j", "123456"))

# 构建查询语句
query = '''
MATCH (h:Pattern)-[r:has_symptom]->(s:Symptom)
RETURN h.name as 证候, s.name as 症状, r.p_os as 共现次数, r.specificity as 特异度
'''
# 执行查询语句
result = graph.run(query)

# 构建字典，key为证候名称，value为证候相关的症状及其共现次数和特异度的列表
data_dict = {}
for record in result:
    h = record['证候']
    s = record['症状']
    co_occurrence = record['共现次数']
    specificity = record['特异度']
    if h not in data_dict:
        data_dict[h] = []
    data_dict[h].append((s, co_occurrence, specificity))


# 计算推荐结果
def recommend(symptoms):
    # 构建查询语句，查询包含所有症状的证候及其对应的共现次数和特异度
    query = '''
    MATCH (h:Pattern)-[r:has_symptom]->(s:Symptom)
    WHERE s.name IN {symptoms}
    WITH h, count(DISTINCT s) AS cnt, sum(r.co_occurrence) AS co_sum, sum(r.specificity) AS sp_sum
    WHERE cnt = {num_symptoms}
    RETURN h.name AS pattern, co_sum, sp_sum
    '''
    query = query.format(symptoms=symptoms, num_symptoms=len(symptoms))

    # 执行查询语句
    result = graph.run(query).to_data_frame()

    # 构建结果列表，每个元素为一个证候及其对应的推荐得分和病机病因
    scores = []
    for record in result.itertuples():
        pattern = record.pattern
        co_sum = record.co_sum
        sp_sum = record.sp_sum
        # 计算朴素贝叶斯得分
        prob = 1.0 / len(data_dict) * np.prod(
            [co_sum / sp_sum if (s, co, sp) in data_dict[pattern] else (1 - co_sum) / sp_sum for s, co, sp in
             data_dict[pattern]])
        # 查询证候对应的病机病因
        etiology_query = '''
        MATCH (p:Pattern)-[r:has_etiology]->(e:Etiology)
        WHERE p.name = {pattern}
        RETURN e.name AS etiology
        '''
        etiology_result = graph.run(etiology_query, pattern=pattern).to_data_frame()
        etiology = etiology_result['etiology'].iloc[0] if not etiology_result.empty else None
        scores.append((pattern, prob, etiology))

    # 根据得分排序并返回前10个证候作为推荐结果
    scores.sort(key=lambda x: x[1], reverse=True)
    return [(pattern, etiology) for pattern, prob, etiology in scores[:10]]


# 计算推荐结果以及评估指标
def evaluate(symptoms, labels):
    recommendations = recommend(symptoms)
    print(recommendations)

    # 计算准确率、召回率和 F1 分数
    tp = len(set(recommendations) & set(labels))
    #     print("tp",tp)
    fp = len(recommendations) - tp
    #     print("fp",fp)
    fn = len(labels) - tp
    #     print("fn",fn)
    precision = tp / (tp + fp)
    #     print("precision",precision)
    recall = tp / (tp + fn)
    #     print("recall",recall)
    f1_score = 2 * precision * recall / (precision + recall)
    #     print("f1_score",f1_score)

    # 将推荐结果、准确率、召回率和 F1 分数作为元组返回
    return precision, recall, f1_score

def evaluate_ndcg(symptoms, true_patterns, k=5):
    # 计算推荐结果
    recommendations = recommend(symptoms)
    # 构建结果列表，每个元素为一个证候及其对应的得分
    scores = []
    for pattern in recommendations:
        if pattern in true_patterns:
            score = 1.0
        else:
            score = 0.0
        scores.append(score)
    # 计算DCG
    dcg = scores[0]
    for i in range(1, min(k, len(scores))):
        dcg += scores[i] / np.log2(i+1)
    # 计算IDCG
    idcg = sorted(scores, reverse=True)[:min(k, len(scores))]
    idcg2 = idcg[0]
    for i in range(1, min(k, len(scores))):
        idcg2 += idcg[i] / np.log2(i+1)
    # 计算NDCG
    if idcg2 == 0:
        return 0.0
    else:
        return dcg / idcg2

if __name__ == '__main__':
#输入想要测试的症状
    symptoms = ['大便稀', '咳嗽', "腰背僵硬疼痛", "咽痛"]
    recommendations = recommend(symptoms)
    print(recommendations)
    true_patterns = ['督脉阻滞', "热毒蕴结"]
    recall, precision, f1 = evaluate(symptoms, true_patterns)
    print("Recall: ", recall)
    print("Precision: ", precision)
    print("F1 Score: ", f1)
    ndcg = evaluate_ndcg(symptoms, true_patterns)
    print("NDCG@5: ", ndcg)