import pandas as pd
from py2neo import Graph, Node, Relationship

# 连接 Neo4j 数据库
graph = Graph("bolt://localhost:7687", auth=("neo4j", "123456"))

# 读取 Excel 文件
df = pd.read_excel("./Data/中医证候VS阳性症状.xlsx", usecols=["symptom", "syndrome"])

# 统计主语实体的就诊次数
k_count = df.groupby("syndrome").size().to_dict()

# 统计主语实体与宾语实体共同出现的就诊次数
ko_count = df.groupby(["syndrome", "symptom"]).size().to_dict()

# 计算特异度的分母
p_s = {}
for s in df["symptom"].unique():
    p_s[s] = sum([ko_count.get((si, s), 0) for si in k_count])

# 创建节点
symptom_nodes = {}
pattern_nodes = {}
for index, row in df.iterrows():
    symptom = row["symptom"]
    pattern = row["syndrome"]

    if symptom not in symptom_nodes:
        symptom_nodes[symptom] = Node("Symptom", name=symptom)
        graph.create(symptom_nodes[symptom])

    if pattern not in pattern_nodes:
        pattern_nodes[pattern] = Node("Pattern", name=pattern, k=k_count[pattern])
        graph.create(pattern_nodes[pattern])

    # 计算共现概率
    k_so = ko_count.get((pattern, symptom), 0)
    p_os = k_so / k_count[pattern]

    # 计算特异度
    p_os_s = k_so / p_s[symptom]
    p_s_o = sum([ko_count.get((si, symptom), 0) for si in k_count]) / sum(k_count.values())
    specificity = p_os / p_s_o

    # 判断是否导入该关系及其四元组属性
    if p_os >= 0.01:
        relationship = Relationship(pattern_nodes[pattern], "has_symptom", symptom_nodes[symptom],
                                    k_so=k_so, p_os=p_os, specificity=specificity)
        graph.create(relationship)
    else:
        print(f"共现概率低于0.01，不导入关系：{pattern_nodes[pattern]} - has_symptom -> {symptom_nodes[symptom]}")




# 读取 Excel 文件
df = pd.read_excel("./Data/中医证候VS方名.xlsx", usecols=["证候", "方名"])

# 统计主语实体的出现次数
k_count = df.groupby("证候").size().to_dict()

# 统计主语实体与宾语实体共同出现的次数
kp_count = df.groupby(["证候", "方名"]).size().to_dict()

# 创建节点
prescription_nodes = {}
pattern_nodes = {}
for index, row in df.iterrows():
    prescription = row["方名"]
    pattern = row["证候"]

    if prescription not in prescription_nodes:
        prescription_nodes[prescription] = Node("Prescription", name=prescription)
        graph.create(prescription_nodes[prescription])

    if pattern not in pattern_nodes:
        pattern_nodes[pattern] = Node("Pattern", name=pattern, k=k_count[pattern])
        graph.create(pattern_nodes[pattern])

    # 计算共现概率
    k_po = kp_count.get((pattern, prescription), 0)
    p_op = k_po / k_count[pattern]

    # 计算特异度
    p_op_o = 0
    if sum(ko_count.values()) > 0:
        p_op_o = k_po / sum(ko_count.values())
    p_o_p = 0
    if sum([ko_count.get((pattern, pi), 0) for pi in k_count]) > 0:
        p_o_p = sum([ko_count.get((pattern, pi), 0) for pi in k_count]) / sum(ko_count.values())
    specificity = 0
    if p_op_o * p_o_p > 0:
        specificity = p_op / (p_op_o * p_o_p)

    # 创建关系及其四元组属性
    relationship = Relationship(pattern_nodes[pattern], "includes", prescription_nodes[prescription],
                                k_po=k_po, p_op=p_op, specificity=specificity)
    graph.merge(relationship)


from py2neo import Graph,Node,Relationship,NodeMatcher
import pandas as pd
graph = Graph("http://localhost:7474", auth=("neo4j", "123456"))  # 旧版本的pyneo2用的在连接方式和新版本不一样
    # graph = Graph("http://localhost:7474", username="root", password='123456')新版本链接方式
graph.delete_all()  # 清除neo4j中原有的结点等所有信息

df1 = pd.read_excel('./Data/中医疾病名VS西医疾病名.xlsx')
for i in df1.index:
    st1 = df1['中医疾病名'].values[i]
    st2 = df1['西医疾病名'].values[i]
    st3 = df1['代码'].values[i]
    st1 = str(st1)
    st2 = str(st2)
    st3 = str(st3)

    st1_node = Node('中医疾病名', name=st1)
    graph.merge(st1_node, '中医疾病名', 'name')
    st2_node = Node('西医疾病名', name=st2)
    graph.merge(st2_node, '西医疾病名', 'name')
    st1_node['代码'] = st3

    yoga = Relationship(st1_node, '对应（西）', st2_node)
    yoga1 = Relationship(st2_node, '对应（中）', st1_node)

    try:
        graph.create(yoga)
        graph.create(yoga1)
        # graph.create(yoga1)
    except:
        continue

df2 = pd.read_excel('./Data/西医疾病名VS病因.xlsx')
for i in df2.index:
    st1 = df2['西医疾病名'].values[i]
    st2 = df2['病因'].values[i]
    st1 = str(st1)
    st2 = str(st2)
    st1_node = Node('西医疾病名',name=st1)
    graph.merge(st1_node,'西医疾病名','name')
    st2_node = Node('病因',name=st2)
    graph.merge(st2_node,'病因','name')
    #数据库中本来存在的数据用st12
    matcher = NodeMatcher(graph)
    nodelist=list(matcher.match('西医疾病名',name=st1))
    if len(nodelist)>0:
        st12_node=nodelist[0]
        Rela= Relationship(st2_node, "由...导致", st12_node)
        Rela1= Relationship(st12_node, "导致", st2_node)
        graph.create(Rela)
        graph.create(Rela1)
    else:
        graph.create(st2_node)
        Rela= Relationship(st2_node, "由...导致",st1_node )
        Rela1= Relationship(st1_node, "导致", st2_node)
        graph.create(Rela)
        graph.create(Rela1)

df3 = pd.read_excel('./Data/病机VS西医疾病名.xlsx')
for i in df3.index:
    st1 = df3['西医疾病名'].values[i]
    st2 = df3['病机'].values[i]
    st1 = str(st1)
    st2 = str(st2)
    st1_node = Node('西医疾病名',name=st1)
    graph.merge(st1_node,'西医疾病名','name')
    st2_node = Node('病机',name=st2)
    graph.merge(st2_node,'病机','name')
    #数据库中本来存在的数据用st12
    matcher = NodeMatcher(graph)
    nodelist=list(matcher.match('西医疾病名',name=st1))
    if len(nodelist)>0:
        st12_node=nodelist[0]
        Rela= Relationship(st2_node, "由...导致", st12_node)
        Rela1= Relationship(st12_node, "导致", st2_node)
        graph.create(Rela)
        graph.create(Rela1)
    else:
        graph.create(st2_node)
        Rela= Relationship(st2_node, "由...导致",st1_node )
        Rela1= Relationship(st1_node, "导致", st2_node)
        graph.create(Rela)
        graph.create(Rela1)

df3 = pd.read_excel('./Data/西医疾病名VS脉象.xlsx')
for i in df3.index:
    st1 = df3['西医疾病名'].values[i]
    st2 = df3['脉象'].values[i]
    st1 = str(st1)
    st2 = str(st2)
    st1_node = Node('西医疾病名',name=st1)
    graph.merge(st1_node,'西医疾病名','name')
    st2_node = Node('脉象',name=st2)
    graph.merge(st2_node,'脉象','name')
    #数据库中本来存在的数据用st12
    matcher = NodeMatcher(graph)
    nodelist=list(matcher.match('西医疾病名',name=st1))
    if len(nodelist)>0:
        st12_node=nodelist[0]
        Rela= Relationship(st2_node, "是..的表现", st12_node)
        Rela1= Relationship(st12_node, "脉象为", st2_node)
        graph.create(Rela)
        graph.create(Rela1)
    else:
        graph.create(st2_node)
        Rela= Relationship(st2_node, "是..的表现",st1_node )
        Rela1= Relationship(st1_node, "脉象为", st2_node)
        graph.create(Rela)
        graph.create(Rela1)

df3 = pd.read_excel('./Data/西医疾病名VS舌象.xlsx')
for i in df3.index:
    st1 = df3['西医疾病名'].values[i]
    st2 = df3['舌象'].values[i]
    st1 = str(st1)
    st2 = str(st2)
    st1_node = Node('西医疾病名',name=st1)
    graph.merge(st1_node,'西医疾病名','name')
    st2_node = Node('舌象',name=st2)
    graph.merge(st2_node,'舌象','name')
    #数据库中本来存在的数据用st12
    matcher = NodeMatcher(graph)
    nodelist=list(matcher.match('西医疾病名',name=st1))
    if len(nodelist)>0:
        st12_node=nodelist[0]
        Rela= Relationship(st2_node, "是..的表现", st12_node)
        Rela1= Relationship(st12_node, "舌象为", st2_node)
        graph.create(Rela)
        graph.create(Rela1)
    else:
        graph.create(st2_node)
        Rela= Relationship(st2_node, "是..的表现",st1_node )
        Rela1= Relationship(st1_node, "舌象为", st2_node)
        graph.create(Rela)
        graph.create(Rela1)

df3 = pd.read_excel('./Data/西医疾病名VS阳性症状.xlsx')
for i in df3.index:
    st1 = df3['西医疾病名'].values[i]
    st2 = df3['阳性症状'].values[i]
    st1 = str(st1)
    st2 = str(st2)
    st1_node = Node('西医疾病名',name=st1)
    graph.merge(st1_node,'西医疾病名','name')
    st2_node = Node('阳性症状',name=st2)
    graph.merge(st2_node,'阳性症状','name')
    #数据库中本来存在的数据用st12
    matcher = NodeMatcher(graph)
    nodelist=list(matcher.match('西医疾病名',name=st1))
    if len(nodelist)>0:
        st12_node=nodelist[0]
        Rela= Relationship(st2_node, "是..的表现", st12_node)
        Rela1= Relationship(st12_node, "阳性症状为", st2_node)
        graph.create(Rela)
        graph.create(Rela1)
    else:
        graph.create(st2_node)
        Rela= Relationship(st2_node, "是..的表现",st1_node )
        Rela1= Relationship(st1_node, "阳性症状为", st2_node)
        graph.create(Rela)
        graph.create(Rela1)

df3 = pd.read_excel('./Data/治则治法VS西医疾病名.xlsx')
for i in df3.index:
    st1 = df3['西医疾病名'].values[i]
    st2 = df3['治则治法'].values[i]
    st1 = str(st1)
    st2 = str(st2)
    st1_node = Node('西医疾病名',name=st1)
    graph.merge(st1_node,'西医疾病名','name')
    st2_node = Node('治则治法',name=st2)
    graph.merge(st2_node,'治则治法','name')
    #数据库中本来存在的数据用st12
    matcher = NodeMatcher(graph)
    nodelist=list(matcher.match('西医疾病名',name=st1))
    if len(nodelist)>0:
        st12_node=nodelist[0]
        Rela= Relationship(st2_node, "被治疗", st12_node)
        Rela1= Relationship(st12_node, "治疗", st2_node)
        graph.create(Rela)
        graph.create(Rela1)
    else:
        graph.create(st2_node)
        Rela= Relationship(st2_node, "被治疗",st1_node )
        Rela1= Relationship(st1_node, "治疗", st2_node)
        graph.create(Rela)
        graph.create(Rela1)

df3 = pd.read_excel('./Data/中医证候VS西医疾病名.xlsx')
for i in df3.index:
    st1 = df3['西医疾病名'].values[i]
    st2 = df3['中医证候'].values[i]
    st1 = str(st1)
    st2 = str(st2)
    st1_node = Node('西医疾病名',name=st1)
    graph.merge(st1_node,'西医疾病名','name')
    st2_node = Node('中医证候',name=st2)
    graph.merge(st2_node,'中医证候','name')
    #数据库中本来存在的数据用st12
    matcher = NodeMatcher(graph)
    nodelist=list(matcher.match('西医疾病名',name=st1))
    if len(nodelist)>0:
        st12_node=nodelist[0]
        Rela= Relationship(st2_node, "被..反映", st12_node)
        Rela1= Relationship(st12_node, "反映", st2_node)
        graph.create(Rela)
        graph.create(Rela1)
    else:
        graph.create(st2_node)
        Rela= Relationship(st2_node, "被..反映",st1_node )
        Rela1= Relationship(st1_node, "反映", st2_node)
        graph.create(Rela)
        graph.create(Rela1)

df3 = pd.read_excel('./Data/中医证候VS脉象.xlsx')
for i in df3.index:
    st1 = df3['中医证候'].values[i]
    st2 = df3['脉象'].values[i]
    st1 = str(st1)
    st2 = str(st2)
    st1_node = Node('中医证候',name=st1)
    graph.merge(st1_node,'中医证候','name')
    st2_node = Node('脉象',name=st2)
    graph.merge(st2_node,'脉象','name')
    #数据库中本来存在的数据用st12
    matcher = NodeMatcher(graph)
    nodelist=list(matcher.match('中医证候',name=st1))
    if len(nodelist)>0:
        st12_node=nodelist[0]
        Rela= Relationship(st2_node, "是..的表现", st12_node)
        Rela1= Relationship(st12_node, "脉象为", st2_node)
        graph.create(Rela)
        graph.create(Rela1)
    else:
        graph.create(st2_node)
        Rela= Relationship(st2_node, "是..的表现",st1_node )
        Rela1= Relationship(st1_node, "脉象为", st2_node)
        graph.create(Rela)
        graph.create(Rela1)

df3 = pd.read_excel('./Data/中医证候VS舌象.xlsx')
for i in df3.index:
    st1 = df3['中医证候'].values[i]
    st2 = df3['舌象'].values[i]
    st1 = str(st1)
    st2 = str(st2)
    st1_node = Node('中医证候',name=st1)
    graph.merge(st1_node,'中医证候','name')
    st2_node = Node('舌象',name=st2)
    graph.merge(st2_node,'舌象','name')
    #数据库中本来存在的数据用st12
    matcher = NodeMatcher(graph)
    nodelist=list(matcher.match('中医证候',name=st1))
    if len(nodelist)>0:
        st12_node=nodelist[0]
        Rela= Relationship(st2_node, "是..的表现", st12_node)
        Rela1= Relationship(st12_node, "舌象为", st2_node)
        graph.create(Rela)
        graph.create(Rela1)
    else:
        graph.create(st2_node)
        Rela= Relationship(st2_node, "是..的表现",st1_node )
        Rela1= Relationship(st1_node, "舌象为", st2_node)
        graph.create(Rela)
        graph.create(Rela1)

df3 = pd.read_excel('./Data/方名vs中药.xlsx')
for i in df3.index:
    st1 = df3['方名'].values[i]
    st2 = df3['中药'].values[i]
    st1 = str(st1)
    st2 = str(st2)
    st1_node = Node('方名',name=st1)
    graph.merge(st1_node,'方名','name')
    st2_node = Node('中药',name=st2)
    graph.merge(st2_node,'中药','name')
    #数据库中本来存在的数据用st12
    matcher = NodeMatcher(graph)
    nodelist=list(matcher.match('方名',name=st1))
    if len(nodelist)>0:
        st12_node=nodelist[0]
        Rela= Relationship(st2_node, "组成", st12_node)
        Rela1= Relationship(st12_node, "由...组成", st2_node)
        graph.create(Rela)
        graph.create(Rela1)
    else:
        graph.create(st2_node)
        Rela= Relationship(st2_node, "组成",st1_node )
        Rela1= Relationship(st1_node, "由...组成", st2_node)
        graph.create(Rela)
        graph.create(Rela1)