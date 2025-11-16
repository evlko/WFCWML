from project.utils.graph import Graph, Vertex
from project.utils.rectangulator import Rect


class GraphBuilder:
    @staticmethod
    def build_graph(rectangles: list[Rect]) -> Graph:
        graph = Graph(
            vertices={i: Vertex(uid=i, rect=rect) for i, rect in enumerate(rectangles)}
        )

        for vertex1 in graph.vertices.values():
            for vertex2 in graph.vertices.values():
                if vertex1.uid != vertex2.uid and vertex2.uid not in vertex1.neighbors:
                    if vertex1.rect.touches(vertex2.rect):
                        vertex1.neighbors.add(vertex2.uid)
                        vertex2.neighbors.add(vertex1.uid)

        return graph
