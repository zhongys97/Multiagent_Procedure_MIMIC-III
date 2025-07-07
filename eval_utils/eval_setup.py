import json
import networkx as nx

MAPPING_JSON_PATH = "/home/hice1/yzhong307/scratch/mimic_iii_1.4/icd9_procedure_mapping.json"


chapters = {
    "0": {"name": "PROCEDURES AND INTERVENTIONS , NOT ELSEWHERE CLASSIFIED",
          "indices": ["0"+str(s) for s in range(0, 1)]},
    "1": {"name": "OPERATIONS ON THE NERVOUS SYSTEM",
          "indices": ["0"+str(s) for s in range(1, 6)]},
    "2": {"name": "OPERATIONS ON THE ENDOCRINE SYSTEM",
          "indices": ["0"+str(s) for s in range(6, 8)]},
    "3": {"name": "OPERATIONS ON THE EYE",
          "indices": ["08", "09"] + [str(s) for s in range(10, 17)]},
    "3A": {"name": "OTHER MISCELLANEOUS DIAGNOSTIC AND THERAPEUTIC PROCEDURES",
          "indices": [str(s) for s in range(17, 18)]},
    "4": {"name": "OPERATIONS ON THE EAR",
          "indices": [str(s) for s in range(18, 21)]},
    "5": {"name": "OPERATIONS ON THE NOSE, MOUTH, AND PHARYNX",
          "indices": [str(s) for s in range(21, 30)]},
    "6": {"name": "OPERATIONS ON THE RESPIRATORY SYSTEM",
          "indices": [str(s) for s in range(30, 35)]},
    "7": {"name": "OPERATIONS ON THE CARDIOVASCULAR SYSTEM",
          "indices": [str(s) for s in range(35, 40)]},
    "8": {"name": "OPERATIONS ON THE HEMIC AND LYMPHATIC SYSTEM",
          "indices": [str(s) for s in range(40, 42)]},
    "9": {"name": "OPERATIONS ON THE DIGESTIVE SYSTEM",
          "indices": [str(s) for s in range(42, 55)]},
    "10": {"name": "OPERATIONS ON THE URINARY SYSTEM",
          "indices": [str(s) for s in range(55, 60)]},
    "11": {"name": "OPERATIONS ON THE MALE GENITAL ORGANS",
          "indices": [str(s) for s in range(60, 65)]},
    "12": {"name": "OPERATIONS ON THE FEMALE GENITAL ORGANS",
          "indices": [str(s) for s in range(65, 72)]},
    "13": {"name": "OBSTETRICAL PROCEDURES",
          "indices": [str(s) for s in range(72, 76)]},
    "14": {"name": "OPERATIONS ON THE MUSCULOSKELETAL SYSTEM",
          "indices": [str(s) for s in range(76, 85)]},
    "14": {"name": "OPERATIONS ON THE MUSCULOSKELETAL SYSTEM",
          "indices": [str(s) for s in range(76, 85)]},
    "15": {"name": "OPERATIONS ON THE INTEGUMENTARY SYSTEM",
          "indices": [str(s) for s in range(85, 87)]},
    "16": {"name": "MISCELLANEOUS DIAGNOSTIC AND THERAPEUTIC PROCEDURES",
          "indices": [str(s) for s in range(87, 100)]},
}

with open(MAPPING_JSON_PATH, "r") as f:
    icd_to_procedure_text = json.load(f)["icd_to_procedure_text"]

icd_4digit_to_procedure_text = {}
ls = set()
for k, v in icd_to_procedure_text.items():
    if len(k) == 1:
        k = "000" + str(k)
    elif len(k) ==  2 :
        k = "00" + str(k)
    elif len(k) == 3:
        k = "0" + str(k)
    icd_4digit_to_procedure_text[k] = v


def get_chapter_name_from_code(code):
    first_two_digits = code[:2]
    for chapter, details in chapters.items():
        if first_two_digits in details["indices"]:
            return details["name"]


def build_icd9_cm_graph():
    """
    Build a graph representation of the ICD-9-CM chapters and procedures.
    
    Returns:
        nx.Graph: A NetworkX graph representing the ICD-9-CM structure.
    """
             
    first_two_digits_to_chapters = {}
    for k, v in chapters.items():
        for two_digits in v["indices"]:
            first_two_digits_to_chapters[two_digits] = v["name"]

    icd_edges = []
                
    for k, v in icd_4digit_to_procedure_text.items():
        node_names = [k[:2], k[:2] + "." + k[2], k[:2] + "." + k[2] + "." + k[3]]
        for i, node_name in enumerate(node_names):
            if i == 0:
                icd_edges.append([first_two_digits_to_chapters[node_name], node_name])
            else:
                icd_edges.append([node_names[i-1], node_name])


    G = nx.Graph()
    for k, v in chapters.items():
        G.add_edge("ICD-9-CM", v["name"])
        
    for icd_edge in icd_edges:
        G.add_edge(icd_edge[0], icd_edge[1])
        
    return G

def get_concept_distance(G, source, target):
    """
    Get the shortest path distance between two ICD-9-CM codes in the graph.
    
    Args:
        G (nx.Graph): The graph representation of ICD-9-CM.
        source (str): The source ICD-9-CM code.
        target (str): The target ICD-9-CM code.
        
    Returns:
        int: The shortest path distance between the two codes.
    """
    try:
        return True, nx.shortest_path_length(G, source=source, target=target)
    except Exception as e:
        return False, float('inf')


if __name__ == "__main__":
      G = build_icd9_cm_graph()

#       source_code = "67"
#       dest_code = "3022"

#       source_code_with_periods = convert_mimic_codes_to_four_digits(source_code)["code_with_periods"]
#       dest_code_with_periods = convert_mimic_codes_to_four_digits(dest_code)["code_with_periods"]

      # print(get_concept_distance(G, source_code_with_periods, target=dest_code_with_periods))
      # True, 8
      # print(nx.diameter(G))
      print(get_concept_distance(G, "30.2.2", target="afaf"))
