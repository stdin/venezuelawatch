#!/usr/bin/env node
/**
 * Community detection using Graphology Louvain algorithm.
 *
 * Reads graph data from JSON file, runs Louvain community detection,
 * returns community assignments and cluster statistics.
 *
 * Usage: node community_detection.js <path-to-graph.json>
 */

const fs = require('fs');
const Graph = require('graphology');
const louvain = require('graphology-communities-louvain');

// Read input file path from command line
const inputPath = process.argv[2];

if (!inputPath) {
  console.error('Usage: node community_detection.js <graph-json-path>');
  process.exit(1);
}

// Read graph data from JSON
const graphData = JSON.parse(fs.readFileSync(inputPath, 'utf8'));

// Build Graphology graph
const graph = new Graph();

// Add nodes
graphData.nodes.forEach(node => {
  graph.addNode(node.id, {
    label: node.label,
    ...node.data
  });
});

// Add edges
graphData.edges.forEach(edge => {
  graph.addEdge(edge.source, edge.target, {
    weight: edge.weight || 1,
    ...edge.data
  });
});

// Run Louvain community detection
louvain.assign(graph, {
  resolution: 1.0,  // Standard resolution parameter
  randomWalk: false  // Deterministic for reproducibility
});

// Extract community assignments
const communities = {};
const clusterStats = {};

graph.forEachNode((nodeId, attrs) => {
  const community = attrs.community;
  communities[nodeId] = community;

  // Calculate cluster statistics
  if (!clusterStats[community]) {
    clusterStats[community] = {
      node_count: 0,
      total_risk: 0,
      sanctioned_count: 0,
      entity_types: {}
    };
  }

  clusterStats[community].node_count += 1;
  clusterStats[community].total_risk += attrs.risk_score || 0;

  if (attrs.sanctions_status) {
    clusterStats[community].sanctioned_count += 1;
  }

  const entityType = attrs.entity_type || 'unknown';
  clusterStats[community].entity_types[entityType] =
    (clusterStats[community].entity_types[entityType] || 0) + 1;
});

// Calculate average risk per cluster
for (const clusterId in clusterStats) {
  const stats = clusterStats[clusterId];
  stats.avg_risk = stats.total_risk / stats.node_count;
}

// Find high-risk cluster (highest average risk score)
let highRiskCluster = null;
let maxAvgRisk = -1;

for (const clusterId in clusterStats) {
  const avgRisk = clusterStats[clusterId].avg_risk;
  if (avgRisk > maxAvgRisk) {
    maxAvgRisk = avgRisk;
    highRiskCluster = clusterId;
  }
}

// Output results as JSON
const result = {
  communities,
  cluster_stats: clusterStats,
  high_risk_cluster: highRiskCluster
};

console.log(JSON.stringify(result));
