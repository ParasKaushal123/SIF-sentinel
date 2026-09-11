// SIF Sentinel — API client (repaired: template literals were stripped in the previous version)
const API_BASE = window.location.origin + '/api/v1';

async function fetchAPI(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    let err = 'API Request Failed';
    try {
      const data = await response.json();
      err = data.detail || err;
    } catch (e) {}
    throw new Error(err);
  }

  if (response.status === 204) return null;
  return response.json();
}

async function getSpatialOverview(datasetId) {
  const q = datasetId ? `?dataset_id=${datasetId}` : '';
  return fetchAPI(`/insights/spatial${q}`);
}

async function getReports(params = {}) {
  const query = new URLSearchParams(params).toString();
  return fetchAPI(`/reports?${query}`);
}

async function getReport(id) {
  return fetchAPI(`/reports/${id}`);
}

async function getInsightsOverview(datasetId) {
  const q = datasetId ? `?dataset_id=${datasetId}` : '';
  return fetchAPI(`/insights/overview${q}`);
}

async function getInsightsPatterns(datasetId) {
  const q = datasetId ? `?dataset_id=${datasetId}` : '';
  return fetchAPI(`/insights/patterns${q}`);
}

async function getPatternReports(patternKey) {
  return fetchAPI(`/insights/patterns/${encodeURIComponent(patternKey)}/reports`);
}

async function getEvidenceGraph(reportId) {
  return fetchAPI(`/reports/${reportId}/evidence-graph`);
}

async function submitReview(reportId, analysisId, expectedVersion, decision, reason, correctedLabel = null) {
  return fetchAPI(`/reports/${reportId}/reviews`, {
    method: 'POST',
    body: JSON.stringify({
      analysis_id: analysisId,
      expected_review_version: expectedVersion,
      decision,
      reason,
      corrected_label: correctedLabel,
    }),
  });
}

async function runLabComparison(leftText, rightText, mode = 'live') {
  return fetchAPI(`/lab/compare`, {
    method: 'POST',
    body: JSON.stringify({ left_text: leftText, right_text: rightText, mode }),
  });
}

window.API = {
  getSpatialOverview,
  getReports,
  getReport,
  getInsightsOverview,
  getInsightsPatterns,
  getPatternReports,
  getEvidenceGraph,
  submitReview,
  runLabComparison,
};
