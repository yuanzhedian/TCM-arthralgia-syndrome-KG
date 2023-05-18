import pandas as pd
from py2neo import Graph

# 连接 Neo4j 数据库
graph = Graph("bolt://localhost:7687", auth=("neo4j", "123456"))

# 计算推荐结果
def recommend(symptoms):
    # 构建查询语句，查询包含所有症状的证候及其对应的共现概率和特异度
    query = '''
    MATCH (h:Pattern)-[r:includes]->(p:Prescription)
    WHERE h.name IN {symptoms}
    RETURN p.name as prescription, r.co_occurrence as co_occurrence, r.specificity as specificity
    '''

    # 执行查询语句
    result = graph.run(query, symptoms=symptoms).to_data_frame()

    # 构建结果列表，每个元素为一个方剂及其对应的推荐得分
    scores = []
    for index, row in result.iterrows():
        prescription = row['prescription']
        co_occurrence = row['co_occurrence']
        specificity = row['specificity']
        # 计算推荐得分
        score = co_occurrence / specificity
        scores.append((prescription, score))

    # 根据得分排序并返回前10个方剂作为推荐结果
    scores.sort(key=lambda x: x[1], reverse=True)
    return [prescription for prescription, score in scores[:10]]


# 输入待推理的证候和西医疾病名
patterns = ['证候1', '证候2']
diseases = ['疾病1', '疾病2']

# 进行推理
prescriptions = recommend(patterns)

# 打印推理结果
print("推理得到的方剂：")
for prescription in prescriptions:
    print(prescription)
