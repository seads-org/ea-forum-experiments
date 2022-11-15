embeddingOptions = {
    chart: {
        zoomType: 'xy',
    },
    plotOptions: {
        bubble: {
            maxSize: '5%'
        }
    },
    xAxis: {
        title: {text: 'Dimension 1'},
        labels: {enabled: false},
        tickLength: 0,
        lineWidth: 1,
        gridLineWidth: 1
    },
    yAxis: {
        title: {text: 'Dimension 2'},
        labels: {enabled: false},
        tickLength: 0,
        lineWidth: 1,
        gridLineWidth: 1
    },
    credits: {enabled: false}
}

heatmapOptions = {
    chart: {
        type: 'heatmap',
        zoomType: 'xy'
    },
    xAxis: {
        gridLineWidth: 0,
        title: null
    },
    yAxis: {
        gridLineWidth: 0,
        title: null
    },
    colorAxis: {
        min: 0,
        max: 1,
        minColor: '#FFFFFF',
        maxColor: '#0868AC'
    },
    credits: {enabled: false}
}

barOptions = {
    chart: {
        zoomType: 'x'
    },
    credits: { enabled: false }
}