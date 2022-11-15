function getHistogramSpec(infoEntries, valueFunc, colorMap, {xTitle, title, binWidth, groupName='Segment'}) {
    return {
        chart: {
            zoomType: 'x'
        },
        title: { text: title },
        xAxis: {
            title: { text: xTitle}
        },
        yAxis: {
            title: { text: 'Number of users' }
        },
        plotOptions: {
            histogram: {
                binWidth: binWidth,
                opacity: 0.75
            }
        },
        series: infoEntries.map(([n, vs]) => {
            return {'id': n + '_base', 'data': valueFunc(vs), 'visible': false, 'showInLegend': false}}
        ).concat(infoEntries.map(([n, vs]) => {
            return {'name': n, 'baseSeries': n + '_base', 'color': colorMap.get(n), type: 'histogram'}}
        )),
        credits: { enabled: false },
        tooltip: {
            formatter() {
                return `${xTitle}: <b>${Math.round(this.point.x * 100) / 100} - ${Math.round(this.point.x2 * 100) / 100}</b><br>` +
                        `Number of users: <b>${this.y}</b>` + `<br>${groupName}: <b>${this.series.name}</b>`;
            }
        }
    }
}

document.addEventListener("DOMContentLoaded", function() {
    fetch('data/user_info.json').then(res => res.json()).then(data => {
        const segments = data.segments;
        const colors = ['#a6cee3','#fdbf6f', '#33a02c', '#fb9a99', '#1f78b4','#e31a1c','#b2df8a'];
        const colorMap = new Map(
            colors.map((c, i) => [segments.segments[i], c])
        );
        Highcharts.chart('user-segments', {
            chart: {
                zoomType: 'xy'
            },
            title: { text: 'User segments' },
            xAxis: {
                categories: segments.segments,
                title: { text: 'Segments' }
            },
            yAxis: {
                title: { text: 'Num. users' }
            },
            legend: { enabled: false },
            credits: { enabled: false },
            series: [{
                type: 'column',
                data: segments.n_users
            }],
            colors: colors,
            tooltip: {
                formatter: function() {
                    return '<strong>' + this.x + '</strong>: ' + this.y + ' users';
                }
            },
            plotOptions: {
                column: {
                    colorByPoint: true
                }
            }
        });

        const info = data.info;
        const infoEntries = Object.entries(info);
        const timeInfo = data.new_vs_old;
        const timeInfoEntries = Object.entries(timeInfo);

        Highcharts.chart('user-scatter', {
            chart: {
                type: 'bubble',
                zoomType: 'xy'
            },
            title: { text: 'User statistics by segment' },
            xAxis: {
                type: 'logarithmic',
                title: { text: 'Num. of posts' }
            },
            yAxis: {
                type: 'logarithmic',
                title: { text: 'Num. of comments' },
                min: 1
            },
            series: infoEntries.map(d => {
                const [name, values] = d;
                return {
                    'name': name,
                    'data': values.n_posts.map((np,i) => ({'x': np, 'y': values.n_comments[i], 'z': Math.log(values.karma[i] + 1), 'i': i})),
                    'color': colorMap.get(name)
            }}),
            plotOptions: {
                bubble: {
                    minSize: '0.01%',
                    maxSize: '2%',
                    jitter: {x: 0.01},
                    events: {
                        click: function(e) {
                            const cInf = info[e.point.series.name];
                            const i = e.point.i;
                            document.getElementById('user-info').innerHTML = `
                                <h3>User <a href=${cInf.pageUrl[i]}>${cInf.username[i]}</a></h3>
                                <p>Num. of posts: ${cInf.n_posts[i]}</p>
                                <p>Num. of comments: ${cInf.n_comments[i]}</p>
                                <p>Karma: ${cInf.karma[i]}</p>
                            `
                        }
                    }
                }
            },
            tooltip: {
                formatter: function() {
                    const cInf = info[this.series.name]
                    return '<strong>' + cInf.username[this.point.i] + '</strong>: ' +
                        this.point.x + ' posts, ' + this.point.y + ' comments, ' + cInf.karma[this.point.i] + ' karma';
                }
            },
            credits: { enabled: false }
        })

        Highcharts.chart(
            'user-lifespan',
            getHistogramSpec(
                infoEntries, vs => vs.lifespan.map(d => d / 365), colorMap,
                {xTitle: 'Num. years since registration', title: 'Time since registration', binWidth: 0.1}
            )
        );

        Highcharts.chart(
            'user-post-rate',
            getHistogramSpec(
                timeInfoEntries, vs => vs.n_posts_norm.map(d => Math.log10(d + 1)), colorMap,
                {xTitle: 'Num. posts, normalized', title: 'Num. posts normalized by time', binWidth: 0.02, groupName: 'Account age'}
            )
        );

        Highcharts.chart(
            'user-comment-rate',
            getHistogramSpec(
                timeInfoEntries, vs => vs.n_comments_norm.map(d => Math.log10(d + 1)), colorMap,
                {xTitle: 'Num. comments, normalized', title: 'Num. comments normalized by time', binWidth: 0.02, groupName: 'Account age'}
            )
        );

        Highcharts.chart(
            'user-karma',
            getHistogramSpec(
                infoEntries, vs => vs.karma.map(d => Math.log10(d + 1)), colorMap,
                {xTitle: 'Log10( Karma )', title: 'Karma', binWidth: 0.1}
            )
        );

        Highcharts.chart(
            'post-score',
            getHistogramSpec(
                infoEntries, vs => vs.post_score_med.map(d => Math.log10(Math.max(d, 0) + 1)), colorMap,
                {xTitle: 'Log10( median post score )', title: 'Post scores', binWidth: 0.1}
            )
        );

        Highcharts.chart(
            'comment-score',
            getHistogramSpec(
                infoEntries, vs => vs.comment_score_med.map(d => Math.log10(Math.max(d, 0) + 1)), colorMap,
                {xTitle: 'Log10( median comment score )', title: 'Comment scores', binWidth: 0.05}
            )
        );
    });

    fetch('data/user_tag_matching.json').then(res => res.json()).then(data => {
        const tag_heatmap = data.tag_heatmap;
        Highcharts.chart('user-tag-heatmap', Highcharts.merge(heatmapOptions, {
            chart: {
                height: '900px',
            },
            title: {
                text: 'Specificity of tags to clusters',
                align: 'left'
            },

            subtitle: {
                text: 'Rows correspond to tags, columns correspond to clusters, and color shows specificity of tags to clusters',
                align: 'left'
            },
            xAxis: {
                categories: tag_heatmap.clust_levels,
            },
            yAxis: {
                categories: tag_heatmap.tag_levels,
            },
            series: [{
                data: tag_heatmap.scores.tag.map((t,i) => [tag_heatmap.scores.cluster[i], t, tag_heatmap.scores.score[i]]),
            }],
            tooltip: {
                formatter: function () {
                    return `Cluster: <b>${this.series.xAxis.categories[this.point.x]}</b><br>` +
                           `Tag: <b>${this.series.yAxis.categories[this.point.y]}</b><br>` +
                           `Score: <b>${this.point.value}</b><br>`;
                }
            }
        }))

        const user_embedding = data.user_embedding;
        const user_info = data.user_info;
        const top_tags_per_clust = data.top_tags_per_clust;
        Highcharts.chart('user-embedding', Highcharts.merge(embeddingOptions, {
            chart: {
                height: '100%'
            },
            title: { text: 'User embedding' },
            plotOptions: {
                scatter: {
                    marker: {radius: 2.5},
                    events: {
                        click: function(e) {
                            const i = e.point.i;
                            document.getElementById('user-tag-info').innerHTML = `
                                <h3>User <a href=${user_info.pageUrl[i]}>${user_info.username[i]}</a></h3>
                                <p>Num. of posts: ${user_info.n_posts[i]}</p>
                                <p>Num. of comments: ${user_info.n_comments[i]}</p>
                                <p>Karma: ${user_info.karma[i]}</p>
                            `
                        }
                    }
                }
            },
            subtitle: { text: 'Each point represents a user, colors show clusters of users (as in the heatmap) and ' +
                'distance between points represent similarities of user preferences. Only active users are used.' },
            series: Object.entries(user_embedding).map(([n, vs]) => ({'name': n, 'data': vs.map(v => ({x: v[1], y: v[2], i: v[0]})), type: 'scatter'})),
            tooltip: {
                formatter() {
                    return `Cluster: <b>${this.series.name}</b><br>` +
                           `User: <b>${user_info.username[this.point.i]}</b><br>` +
                           `Tags: <b>${top_tags_per_clust[this.series.name]}</b><br>`;
                }
            }
        }))

        const tag_embedding = data.tag_embedding;
        const tag_info = data.tag_info;
        Highcharts.chart('tag-embedding', Highcharts.merge(embeddingOptions, {
            chart: {
                height: '100%'
            },
            title: { text: 'Tag embedding' },
            plotOptions: {
                scatter: {
                    marker: {radius: 2.5}
                }
            },
            subtitle: { text: 'Each point represents a user, colors show clusters of users (as in the heatmap) and ' +
                'distance between points represent similarities of user preferences. Only active users are used.' },
            series: Object.entries(tag_embedding).map(([n, vs]) => ({
                name: n, type: 'bubble',
                dataLabels: {
                    enabled: true,
                    format: '{point.tag}',
                    style: {
                        'fontSize': '7px'
                    }
                },
                data: vs.map(v => ({x: v[1], y: v[2], z: Math.log(tag_info.n_posts[v[0]]), i: v[0], tag: tag_info.tag[v[0]]}))
            })),
            tooltip: {
                formatter() {
                    return `Tag: <b>${tag_info.tag[this.point.i]}</b><br>` +
                           `Cluster: <b>${this.series.name >= 0 ? this.series.name : 'mixed'}</b><br>` +
                           `Num. posts: <b>${tag_info.n_posts[this.point.i]}</b><br>`;
                }
            }
        }))

        const n_users_per_clust = data.n_users_per_clust;
        Highcharts.chart('cluster-size-bar', Highcharts.merge(barOptions, {
            colorAxis: {},
            title: { text: 'Number of users per cluster' },
            xAxis: {
                categories: n_users_per_clust.map((_, i) => i),
                title: { text: 'Cluster' }
            },
            yAxis: {
                title: { text: 'Number of users' }
            },
            series: [{data: n_users_per_clust, type: 'column'}],
            legend: { enabled: false },
            tooltip: {
                formatter() {
                    return `Cluster: <b>${this.x}</b><br>` +
                           `Num. users: <b>${this.y}</b><br>`;
                }
            }
        }))
    })
});