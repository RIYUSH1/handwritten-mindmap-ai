import os
import logging
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MindMapGenerator")


def wrap_text(text: str, max_words_per_line: int = 3) -> str:
    """
    Splits long phrases/sentences into multi-line strings
    so that visual nodes auto-wrap and avoid visual truncation.
    """
    words = text.split()
    lines = []
    for i in range(0, len(words), max_words_per_line):
        lines.append(" ".join(words[i:i + max_words_per_line]))
    return "\n".join(lines)


def generate_mindmap_from_concepts(
    main_topic: str,
    topic_groups: dict,
    theme: str = "Sunset Amber",
    node_size: int = 18,
    physics_enabled: bool = True,
    spring_length: int = 300,
    spring_strength: float = 0.04,
    edge_smooth: bool = True
):
    """
    Generates both:
    1. Static mind map PNG image (theme-colored NetworkX graph)
    2. Premium interactive canvas HTML file (PyVis dynamic canvas graph)
    
    Args:
        main_topic (str): The root/center mind map node.
        topic_groups (dict): Dictionary mapping cluster IDs to text concepts:
            {
               0: ["Extracted sentence 1", "Extracted sentence 2"],
               1: ["Extracted sentence 3"]
            }
        theme (str): Active SaaS theme (Sunset Amber, Cyberpunk Neon, Ocean Breeze, Forest Emerald).
        node_size (int): Base font size for nodes.
        physics_enabled (bool): Toggle motion forces.
        spring_length (int): Distance between nodes.
        spring_strength (float): Elastic rigidness of spring forces.
        edge_smooth (bool): Enable curved connections.
    """
    os.makedirs("output", exist_ok=True)

    # 1. Detailed Initial Logging
    logger.info("=========================================================")
    logger.info(f"MindMap request received for Root Node: '{main_topic}'")
    logger.info(f"Theme Scheme: {theme} | Physics Enabled: {physics_enabled}")
    logger.info(f"Visual Spring Length: {spring_length} | Rigidity: {spring_strength}")
    
    num_clusters = len(topic_groups)
    total_concept_nodes = sum(len(c) for c in topic_groups.values())
    total_nodes_to_map = 1 + num_clusters + total_concept_nodes
    logger.info(f"Total Clusters: {num_clusters} | Total Subconcept Nodes: {total_concept_nodes}")
    logger.info(f"Graph Construction Target: {total_nodes_to_map} total Nodes")
    logger.info("=========================================================")

    # -------------------------------------------------
    # THEME SCHEME DESIGN SYSTEM
    # -------------------------------------------------
    themes = {
        "Sunset Amber": {
            "bg": "#120d0b",
            "main_color": "#ff7b2c",
            "cluster_colors": ["#ff5e3a", "#f97316", "#fdba74", "#fca5a5", "#ea580c"],
            "node_bg": "#1f1f1f",
            "node_text": "#f8fafc",
            "edge_color": "rgba(255, 123, 44, 0.4)",
            "main_text": "#ffffff",
            "cluster_text": "#ffffff",
            "static_main": "#ff7b2c",
            "static_cluster": "#ff5e3a",
            "static_concept": "#1f1f1f",
            "static_edge": "#ff7b2c"
        },
        "Cyberpunk Neon": {
            "bg": "#090d16",
            "main_color": "#f43f5e",
            "cluster_colors": ["#06b6d4", "#a855f7", "#ec4899", "#10b981", "#eab308"],
            "node_bg": "#161c2d",
            "node_text": "#f8fafc",
            "edge_color": "rgba(244, 63, 94, 0.4)",
            "main_text": "#ffffff",
            "cluster_text": "#ffffff",
            "static_main": "#f43f5e",
            "static_cluster": "#06b6d4",
            "static_concept": "#cbd5e1",
            "static_edge": "#f43f5e"
        },
        "Ocean Breeze": {
            "bg": "#0b151a",
            "main_color": "#0d9488",
            "cluster_colors": ["#38bdf8", "#2dd4bf", "#34d399", "#818cf8", "#60a5fa"],
            "node_bg": "#0f2027",
            "node_text": "#f0fdfa",
            "edge_color": "rgba(13, 148, 136, 0.4)",
            "main_text": "#ffffff",
            "cluster_text": "#ffffff",
            "static_main": "#0d9488",
            "static_cluster": "#38bdf8",
            "static_concept": "#9eeaf9",
            "static_edge": "#0d9488"
        },
        "Forest Emerald": {
            "bg": "#09120e",
            "main_color": "#10b981",
            "cluster_colors": ["#84cc16", "#14b8a6", "#22c55e", "#a3e635", "#65a30d"],
            "node_bg": "#0c1f20",
            "node_text": "#f0fdf4",
            "edge_color": "rgba(16, 185, 129, 0.4)",
            "main_text": "#ffffff",
            "cluster_text": "#ffffff",
            "static_main": "#10b981",
            "static_cluster": "#84cc16",
            "static_concept": "#bbf7d0",
            "static_edge": "#10b981"
        }
    }

    cfg = themes.get(theme, themes["Sunset Amber"])

    # -------------------------------------------------
    # 1. STATIC GRAPH GENERATION (PNG) – NETWORKX
    # -------------------------------------------------
    try:
        logger.info("STAGE: Generating static NetworkX PNG mindmap...")
        G = nx.Graph()
        
        # Add root node
        G.add_node(main_topic)
        logger.info(f"NetworkX: Mapped Main Root Node '{main_topic}'")

        # Build connections
        edge_count = 0
        for cluster_id, concepts in topic_groups.items():
            cluster_node = f"Group {cluster_id + 1}"
            G.add_edge(main_topic, cluster_node)
            edge_count += 1

            for concept in concepts:
                # Wrap long node texts for presentation
                wrapped_concept = wrap_text(concept, 4)
                G.add_edge(cluster_node, wrapped_concept)
                edge_count += 1

        logger.info(f"NetworkX: Node mapping completed. {len(G.nodes())} Nodes & {edge_count} Edges mapped successfully.")

        plt.figure(figsize=(14, 11), facecolor=cfg["bg"])
        pos = nx.spring_layout(G, seed=42, k=1.3)

        # Color mapping for NetworkX nodes
        color_map = []
        for node in G.nodes():
            if node == main_topic:
                color_map.append(cfg["static_main"])
            elif any(node == f"Group {cluster_id + 1}" for cluster_id in topic_groups.keys()):
                color_map.append(cfg["static_cluster"])
            else:
                color_map.append(cfg["static_concept"])

        # Determine font color depending on theme brightness
        font_color = "black" if theme in ("Ocean Breeze", "Forest Emerald") else "white"

        nx.draw(
            G,
            pos,
            with_labels=True,
            node_color=color_map,
            node_size=2800,
            font_size=8,
            font_color=font_color,
            font_weight="bold",
            edge_color=cfg["static_edge"],
            width=2.0
        )

        plt.savefig("output/mindmap.png", bbox_inches="tight", facecolor=cfg["bg"])
        plt.close()
        logger.info(f"Static PNG mindmap generated successfully at 'output/mindmap.png' (Size: {os.path.getsize('output/mindmap.png')} bytes).")
    except Exception as e:
        logger.error(f"Failed to generate static PNG mindmap: {e}", exc_info=True)

    # -------------------------------------------------
    # 2. INTERACTIVE GRAPH GENERATION (HTML Canvas) – PYVIS
    # -------------------------------------------------
    try:
        logger.info("STAGE: Generating premium PyVis HTML interactive canvas...")
        net = Network(
            height="700px",
            width="100%",
            bgcolor=cfg["bg"],
            font_color="white"
        )

        # Dynamic JSON-based VisJS Physics configuration
        smooth_type = "continuous" if edge_smooth else "false"
        physics_options = f"""
        {{
          "physics": {{
            "enabled": {str(physics_enabled).lower()},
            "barnesHut": {{
              "gravitationalConstant": -60000,
              "springLength": {spring_length},
              "springConstant": {spring_strength},
              "avoidOverlap": 0.85
            }}
          }},
          "nodes": {{
            "borderWidth": 2,
            "borderWidthSelected": 4
          }},
          "edges": {{
            "smooth": {{
              "enabled": {str(edge_smooth).lower()},
              "type": "{smooth_type}"
            }}
          }}
        }}
        """
        net.set_options(physics_options)
        logger.info("PyVis physics and layout options initialized.")

        # ADD ROOT (MAIN TOPIC) NODE
        logger.info(f"PyVis: Adding Main Topic node: '{main_topic}'")
        net.add_node(
            main_topic,
            label=wrap_text(main_topic, 2),
            shape="box",
            color=cfg["main_color"],
            font={
                "size": node_size + 5,
                "bold": True,
                "color": cfg["main_text"]
            },
            margin=24,
            shadow={
                "enabled": True,
                "color": cfg["main_color"],
                "size": 20,
                "x": 0,
                "y": 0
            }
        )

        # ADD CLUSTERS AND SUB-CONCEPTS
        mapped_cluster_count = 0
        mapped_concept_count = 0
        mapped_edge_count = 0
        
        for idx, (cluster_id, concepts) in enumerate(topic_groups.items()):
            cluster_name = f"Group {cluster_id + 1}"
            color = cfg["cluster_colors"][idx % len(cfg["cluster_colors"])]

            # A. Add Cluster Group Node
            logger.info(f"PyVis: Adding Cluster Node: '{cluster_name}'")
            net.add_node(
                cluster_name,
                label=cluster_name,
                shape="box",
                color=color,
                font={
                    "size": node_size + 1,
                    "bold": True,
                    "color": cfg["cluster_text"]
                },
                margin=18,
                shadow={
                    "enabled": True,
                    "color": color,
                    "size": 14,
                    "x": 0,
                    "y": 0
                }
            )
            mapped_cluster_count += 1

            # Link Root to Cluster Node
            net.add_edge(main_topic, cluster_name, color=cfg["edge_color"], width=3.5)
            mapped_edge_count += 1

            # B. Add Individual Concept Nodes under this Cluster
            logger.info(f"PyVis: Mapping {len(concepts)} subconcepts for '{cluster_name}'...")
            for concept in concepts:
                wrapped_concept = wrap_text(concept, 3)

                net.add_node(
                    concept,
                    label=wrapped_concept,
                    title=concept,  # Full description tooltip on mouse hover
                    shape="box",
                    color=cfg["node_bg"],
                    font={
                        "size": node_size - 2,
                        "color": cfg["node_text"]
                    },
                    margin=15,
                    shadow={
                        "enabled": True,
                        "color": "rgba(255, 255, 255, 0.05)",
                        "size": 8,
                        "x": 0,
                        "y": 0
                    }
                )
                mapped_concept_count += 1

                # Link Cluster to Concept Node
                net.add_edge(cluster_name, concept, color=cfg["edge_color"], width=1.5)
                mapped_edge_count += 1

        logger.info(f"PyVis: Total mapped clusters: {mapped_cluster_count} | Mapped concepts: {mapped_concept_count} | Total edges: {mapped_edge_count}")

        # Save the finalized PyVis graph output
        output_html = "output/interactive_mindmap.html"
        logger.info(f"STAGE: Exporting PyVis interactive graph to file '{output_html}'...")
        net.save_graph(output_html)
        logger.info(f"Interactive HTML graph exported successfully to '{output_html}' (Size: {os.path.getsize(output_html)} bytes).")
        
    except Exception as e:
        logger.error(f"Failed to generate interactive HTML mindmap: {e}", exc_info=True)
        raise RuntimeError(f"❌ PyVis Canvas generation crashed. Details: {str(e)}")
