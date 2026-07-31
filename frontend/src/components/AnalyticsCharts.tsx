import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import {
  getCategoryTrends,
  getDepartmentPerformance,
  getResolutionTimes,
  TrendsResponse,
  DepartmentPerformanceResponse,
  ResolutionTimesResponse
} from '../api/admin';
import './AnalyticsCharts.css';

interface AnalyticsChartsProps {
  compact?: boolean;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

const AnalyticsCharts: React.FC<AnalyticsChartsProps> = ({ compact = false }) => {
  const [trendsData, setTrendsData] = useState<TrendsResponse | null>(null);
  const [departmentData, setDepartmentData] = useState<DepartmentPerformanceResponse | null>(null);
  const [resolutionData, setResolutionData] = useState<ResolutionTimesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState(30);

  useEffect(() => {
    fetchAnalyticsData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeRange]);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [trends, departments, resolutions] = await Promise.all([
        getCategoryTrends({ days: timeRange, interval: 'day' }),
        getDepartmentPerformance({ days: timeRange }),
        getResolutionTimes({ days: timeRange })
      ]);

      setTrendsData(trends);
      setDepartmentData(departments);
      setResolutionData(resolutions);
    } catch (err: any) {
      console.error('Error fetching analytics data:', err);
      setError(err.response?.data?.error || 'Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="analytics-loading">
        <p>Loading analytics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-error">
        <p>Error: {error}</p>
        <button onClick={fetchAnalyticsData}>Retry</button>
      </div>
    );
  }

  // Prepare category trends data for line chart
  const prepareTrendsChartData = () => {
    if (!trendsData) return [];

    const categories = Object.keys(trendsData.trends);
    const dates = trendsData.trends[categories[0]]?.map(d => d.date) || [];

    return dates.map(date => {
      const dataPoint: any = { date };
      categories.forEach(category => {
        const trend = trendsData.trends[category].find(t => t.date === date);
        dataPoint[category] = trend?.count || 0;
      });
      return dataPoint;
    });
  };

  // Prepare category totals for pie chart
  const prepareCategoryPieData = () => {
    if (!trendsData) return [];

    return Object.entries(trendsData.totals).map(([category, count]) => ({
      name: category,
      value: count
    }));
  };


  // Prepare resolution time data by category
  const prepareResolutionByCategory = () => {
    if (!resolutionData) return [];

    return Object.entries(resolutionData.by_category).map(([category, stats]) => ({
      name: category,
      avgHours: stats.avg_hours,
      count: stats.count
    }));
  };

  // Prepare resolution time data by priority
  const prepareResolutionByPriority = () => {
    if (!resolutionData) return [];

    return Object.entries(resolutionData.by_priority).map(([priority, stats]) => ({
      name: priority,
      avgHours: stats.avg_hours,
      count: stats.count
    }));
  };

  const trendsChartData = prepareTrendsChartData();
  const categoryPieData = prepareCategoryPieData();
  const resolutionByCategoryData = prepareResolutionByCategory();
  const resolutionByPriorityData = prepareResolutionByPriority();

  return (
    <div className={`analytics-charts ${compact ? 'compact' : ''}`}>
      {/* Time Range Filter */}
      <div className="analytics-filters">
        <label>Time Period:</label>
        <select value={timeRange} onChange={(e) => setTimeRange(parseInt(e.target.value))}>
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {!compact && (
        <>
          {/* Category Trends Line Chart */}
          <div className="chart-section">
            <h3>Category-wise Complaint Trends</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trendsChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                {Object.keys(trendsData?.trends || {}).map((category, index) => (
                  <Line
                    key={category}
                    type="monotone"
                    dataKey={category}
                    stroke={COLORS[index % COLORS.length]}
                    strokeWidth={2}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Category Distribution Pie Chart */}
          <div className="chart-section">
            <h3>Complaint Distribution by Category</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={categoryPieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {categoryPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      {/* Department Performance Table */}
      <div className="chart-section">
        <h3>Department Performance</h3>
        <div className="department-table-container">
          <table className="department-table">
            <thead>
              <tr>
                <th>Department</th>
                <th>Total</th>
                <th>Pending</th>
                <th>Resolved</th>
                <th>Avg Resolution (hrs)</th>
                <th>SLA Compliance</th>
              </tr>
            </thead>
            <tbody>
              {departmentData?.departments.map((dept, index) => (
                <tr key={index}>
                  <td>{dept.department.replace(' Department', '')}</td>
                  <td>{dept.total_complaints}</td>
                  <td className="pending">{dept.pending_complaints}</td>
                  <td className="resolved">{dept.resolved_complaints}</td>
                  <td>{dept.avg_resolution_time_hours.toFixed(1)}</td>
                  <td>
                    <span className={`sla-badge ${dept.sla_compliance_rate >= 90 ? 'good' : dept.sla_compliance_rate >= 75 ? 'warning' : 'poor'}`}>
                      {dept.sla_compliance_rate.toFixed(1)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {!compact && (
        <>
          {/* Resolution Time by Category */}
          <div className="chart-section">
            <h3>Average Resolution Time by Category</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={resolutionByCategoryData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                <YAxis label={{ value: 'Hours', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Bar dataKey="avgHours" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Resolution Time by Priority */}
          <div className="chart-section">
            <h3>Average Resolution Time by Priority</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={resolutionByPriorityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis label={{ value: 'Hours', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Bar dataKey="avgHours" fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Overall Statistics */}
          <div className="chart-section">
            <h3>Overall Statistics</h3>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-value">{resolutionData?.overall.count || 0}</div>
                <div className="stat-label">Total Resolved</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{resolutionData?.overall.avg_hours.toFixed(1) || 0}</div>
                <div className="stat-label">Avg Resolution (hrs)</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{resolutionData?.overall.min_hours.toFixed(1) || 0}</div>
                <div className="stat-label">Fastest Resolution (hrs)</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{resolutionData?.overall.max_hours.toFixed(1) || 0}</div>
                <div className="stat-label">Slowest Resolution (hrs)</div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default AnalyticsCharts;
