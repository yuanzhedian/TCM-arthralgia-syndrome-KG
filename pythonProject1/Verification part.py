import pandas as pd
from py2neo import Graph

# 连接 Neo4j 数据库
graph = Graph("bolt://localhost:7687", auth=("neo4j", "123456"))

# 根据症状推理最可能的西医疾病名
def infer_disease(symptoms):
    # 构建查询语句，查询包含所有症状的西医疾病名及其对应的共现概率和特异度
    query = '''
    MATCH (d:Disease)-[r:has_symptom]->(s:Symptom)
    WHERE s.name IN {symptoms}
    RETURN d.name AS disease, sum(r.co_occurrence) AS co_occurrence, sum(r.specificity) AS specificity
    '''

    # 执行查询语句
    result = graph.run(query, symptoms=symptoms).to_data_frame()

    # 根据共现概率和特异度计算推荐得分
    result['score'] = result['co_occurrence'] / result['specificity']

    # 根据得分排序并返回最可能的西医疾病名
    disease = result.sort_values('score', ascending=False).iloc[0]['disease']
    return disease


# 根据西医疾病名推理最可能的方剂
def infer_prescription(disease):
    # 构建查询语句，查询包含指定西医疾病名的方剂及其对应的共现概率和特异度
    query = '''
    MATCH (d:Disease)-[r:has_prescription]->(p:Prescription)
    WHERE d.name = {disease}
    RETURN p.name AS prescription, r.co_occurrence AS co_occurrence, r.specificity AS specificity
    '''

    # 执行查询语句
    result = graph.run(query, disease=disease).to_data_frame()

    # 根据共现概率和特异度计算推荐得分
    result['score'] = result['co_occurrence'] / result['specificity']

    # 根据得分排序并返回最可能的方剂
    prescription = result.sort_values('score', ascending=False).iloc[0]['prescription']
    return prescription


# 输入症状，进行推荐
def recommend(symptoms):
    # 推理最可能的西医疾病名
    disease = infer_disease(symptoms)

    # 推理最可能的方剂
    prescription = infer_prescription(disease)

    return prescription


# 示例用法
symptoms = ['咳嗽', '发热']
recommendation = recommend(symptoms)
print(recommendation)
