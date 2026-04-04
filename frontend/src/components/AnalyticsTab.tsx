import { useEffect, useState } from 'react';
import {
  Box, Card, CardContent, Grid, Typography, LinearProgress,
} from '@mui/material';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie,
  Cell, Legend,
} from 'recharts';
import { getOverview, getByClass, getByStorey, getCompleteness, getIssuesSummary } from '../api/analytics';
import type { AnalyticsOverview, ClassStats, StoreyStats, Completeness, IssuesSummary } from '../types';

const COLORS = ['#1565c0', '#f57c00', '#2e7d32', '#c62828', '#6a1b9a', '#00838f', '#4e342e', '#546e7a'];

const CLASS_TRANSLATIONS: Record<string, string> = {
  'Wall': 'Стена',
  'WallStandardCase': 'Стена (ст)',
  'Door': 'Дверь',
  'Window': 'Окно',
  'Slab': 'Перекрытие',
  'Column': 'Колонна',
  'Beam': 'Балка',
  'Stair': 'Лестница',
  'StairFlight': 'Лестничный марш',
  'Roof': 'Крыша',
  'Space': 'Помещение',
  'BuildingElementProxy': 'Сборный элемент',
  'Railing': 'Ограждение',
  'Covering': 'Покрытие',
  'CurtainWall': 'Навесная стена',
  'Furniture': 'Мебель',
  'Member': 'Элемент каркаса',
  'Plate': 'Пластина',
  'FlowTerminal': 'Оборудование',
  'FlowSegment': 'Труба/Воздуховод',
  'FlowFitting': 'Фитинг',
  'PipeSegment': 'Труба',
  'PipeFitting': 'Фитинг трубы',
  'DuctSegment': 'Воздуховод',
  'DuctFitting': 'Фитинг возд.',
  'Site': 'Участок',
  'Building': 'Здание',
  'BuildingStorey': 'Этаж',
  'OpeningElement': 'Проём'
};

function translateIfcClass(className: string): string {
  const stripped = className.replace('Ifc', '');
  return CLASS_TRANSLATIONS[stripped] || stripped;
}

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <Card>
      <CardContent>
        <Typography color="text.secondary" variant="body2">{label}</Typography>
        <Typography variant="h4">{value}</Typography>
        {sub && <Typography variant="caption" color="text.secondary">{sub}</Typography>}
      </CardContent>
    </Card>
  );
}

export default function AnalyticsTab({ projectId }: { projectId: string }) {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [byClass, setByClass] = useState<ClassStats[]>([]);
  const [byStorey, setByStorey] = useState<StoreyStats[]>([]);
  const [completeness, setCompleteness] = useState<Completeness | null>(null);
  const [issuesSummary, setIssuesSummary] = useState<IssuesSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getOverview(projectId).then(r => setOverview(r.data)),
      getByClass(projectId).then(r => setByClass(r.data)),
      getByStorey(projectId).then(r => setByStorey(r.data)),
      getCompleteness(projectId).then(r => setCompleteness(r.data)),
      getIssuesSummary(projectId).then(r => setIssuesSummary(r.data)),
    ]).finally(() => setLoading(false));
  }, [projectId]);

  if (loading) return <LinearProgress />;
  if (!overview) return <Typography>Нет данных</Typography>;

  const classData = byClass.slice(0, 10).map(c => ({ 
    name: translateIfcClass(c.ifc_class), 
    count: c.count, 
    area: Math.round(c.total_area) 
  }));

  // Функция для извлечения числа из названия этажа для сортировки
  const extractStoreyNumber = (name: string) => {
    if (!name) return 0;
    const lower = name.toLowerCase();
    if (lower.includes('кровля') || lower.includes('крыша')) return 1000;
    if (lower.includes('чердак')) return 999;
    if (lower.includes('подвал') || lower.includes('паркинг') || lower.includes('цоколь')) return -999;
    if (lower.includes('не назначен') || lower === '?') return 0;

    const match = name.match(/-?\d+/);
    return match ? parseInt(match[0], 10) : 0;
  };

  const formatStoreyName = (name: string) => {
    if (!name || name === '?' || name.toLowerCase() === 'не назначен') return 'Уровень 0';
    // Заменяем "уровень-1" на "-1 этаж", "уровень 2" на "2 этаж"
    return name.replace(/уровень\s*(-?\d+)/i, '$1 этаж');
  };

  const storeyData = byStorey
    .map(s => ({
        name: formatStoreyName(s.storey_name),
        elements: s.element_count,
        problems: s.problematic_count,
        rawName: s.storey_name || ''
    }))
    // Сортировка по убыванию: индексы с большими значениями (Чердак, высокие этажи)
    // будут в начале массива и отрисуются в самом верху графика
    .sort((a, b) => extractStoreyNumber(b.rawName) - extractStoreyNumber(a.rawName));

  const issuesBySeverity = issuesSummary ? Object.entries(issuesSummary.by_severity).map(([name, value]) => ({ name, value })) : [];

  return (
    <Box>
      <Typography variant="h5" gutterBottom>Аналитика</Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}><StatCard label="Элементы" value={overview.total_elements} /></Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}><StatCard label="Здания" value={overview.total_buildings} /></Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}><StatCard label="Этажи" value={overview.total_storeys} /></Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}><StatCard label="Помещения" value={overview.total_spaces} /></Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}><StatCard label="Замечания" value={overview.total_issues} /></Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}><StatCard label="Площадь" value={`${overview.total_area.toFixed(0)}`} sub="м²" /></Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 8 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Элементы по классам IFC</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={classData}>
                  <XAxis dataKey="name" angle={-30} textAnchor="end" height={60} fontSize={12} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#1565c0" name="Количество" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Замечания по критичности</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie data={issuesBySeverity} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
                    {issuesBySeverity.map((_, i) => (
                      <Cell key={i} fill={['#c62828', '#f57c00', '#1565c0'][i % 3]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Элементы по этажам</Typography>
              {/* Используем динамическую высоту, чтобы графики не сплющивало и этажи не пропадали */}
              <ResponsiveContainer width="100%" height={Math.max(300, storeyData.length * 40)}>
                <BarChart data={storeyData} layout="vertical">
                  <XAxis type="number" />
                  {/* interval={0} гарантирует что Recharts не будет скрывать лейблы этажей из-за нехватки места */}
                  <YAxis dataKey="name" type="category" width={120} fontSize={12} interval={0} />
                  <Tooltip />
                  <Bar dataKey="elements" fill="#1565c0" name="Элементы" />
                  <Bar dataKey="problems" fill="#f57c00" name="Проблемные" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Полнота данных</Typography>
              {completeness && (
                <Box>
                  {[
                    ['Наименование', completeness.pct_name],
                    ['Тип', completeness.pct_type],
                    ['Этаж', completeness.pct_storey],
                    ['Материал', completeness.pct_material],
                    ['Количества', completeness.pct_quantities],
                  ].map(([label, pct]) => (
                    <Box key={label as string} sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Typography variant="body2">{label as string}</Typography>
                        <Typography variant="body2" fontWeight={600}>{(pct as number).toFixed(1)}%</Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={pct as number}
                        color={(pct as number) > 80 ? 'success' : (pct as number) > 50 ? 'warning' : 'error'}
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                    </Box>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
