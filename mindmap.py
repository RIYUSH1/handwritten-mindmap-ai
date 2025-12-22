import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
import os

def generate_mindmap(keywords, main_topic):
    os.makedirs("output", exist_ok=True)

    # -------- STATIC GRAPH (PNG) --------
    G = nx.Graph()
    G.add_node(main_topic)

    for kw in keywords:
        G.add_edge(main_topic, kw)

    plt.figure(figsize=(10, 8))
    nx.draw(
        G,
        with_labels=True,
        node_color="#93c5fd",
        node_size=2500,
        font_size=10
    )
    plt.savefig("output/mindmap.png", bbox_inches="tight")
    plt.close()

    # -------- INTERACTIVE GRAPH (HTML) --------
    net = Network(
        height="600px",
        width="100%",
        bgcolor="#0f172a",
        font_color="white"
    )

    net.add_node(main_topic, label=main_topic, color="#2563eb", size=35)

    for kw in keywords:
        net.add_node(kw, label=kw, color="#facc15", size=20)
        net.add_edge(main_topic, kw)

    net.toggle_physics(True)
    net.show_buttons(filter_=["physics"])

    net.save_graph("output/interactive_mindmap.html")
