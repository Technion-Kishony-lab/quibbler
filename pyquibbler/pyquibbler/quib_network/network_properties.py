# Define style and layout of quib network

NETWORK_STYLE = \
    [
        {
            'selector': 'edge',
            'style': {
                'width': 3,
                'line-color': '#909090'
            }
        },

        {
            'selector': 'edge.directed',
            'style': {
                'curve-style': 'bezier',
                'target-arrow-shape': 'triangle',
                'target-arrow-color': '#909090'
            }
        },

        {
            'selector': 'edge.data_source',
            'style': {
                'line-color': '#00D7FF',
                'target-arrow-color': '#00D7FF'
            }
        },

        {
            'selector': 'node',
            'css': {
                'content': 'data(name)',
                'text-valign': 'center',
                'text-halign': 'right',
                'background-color': '#00D7FF',
                'border-color': 'black',
                'font-size': 12,
                'border-width': 0.5,
            }
        },

        {
            'selector': 'node.iquib',
            'css': {
                'shape': "diamond",
                'text-valign': 'top',
                'text-halign': 'center',
            }
        },

        {
            'selector': 'node.focal',
            'css': {
                'background-color': '#D61C4E',
            }
        },

        {
            'selector': 'node.null',
            'css': {
                'background-color': '#C0C0C0',
            }
        },

        {
            'selector': 'node.graphics',
            'css': {
                'shape': "hexagon",
            }
        },

        {
            'selector': 'node.overridden',
            'css': {
                'border-color': '#5800FF',
                'border-width': 6,
                'border-style': 'dashed',
            }
        },

        {
            'selector': 'node.hidden',
            'css': {
                'background-color': '#A0A0A0',
                'width': 10,
                'height': 10,
                'text-valign': 'top',
                'text-halign': 'center',
            }
        },

    ]

NETWORK_LAYOUT = {
    'name': 'dagre',  # can try: dagre elk
    'spacingFactor': 1.2,
    'nodeSpacing': 2,
    'edgeLengthVal': 0,
}
