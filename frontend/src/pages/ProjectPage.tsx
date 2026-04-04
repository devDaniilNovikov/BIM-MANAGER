import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box, Tab, Tabs, Typography, IconButton, LinearProgress, Breadcrumbs, Link,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { getProject } from '../api/projects';
import type { ProjectDetail } from '../types';
import ViewerTab from '../components/ViewerTab';
import StructureTab from '../components/StructureTab';
import ElementsTab from '../components/ElementsTab';
import IssuesTab from '../components/IssuesTab';
import AnalyticsTab from '../components/AnalyticsTab';
import ExportTab from '../components/ExportTab';
import QualityTab from '../components/QualityTab';

export default function ProjectPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [tab, setTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (!projectId) return;
    setLoading(true);
    getProject(projectId).then(r => setProject(r.data)).finally(() => setLoading(false));
  }, [projectId]);

  if (loading) return <LinearProgress />;
  if (!project || !projectId) return <Typography>Проект не найден</Typography>;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <IconButton onClick={() => navigate('/')} sx={{ mr: 1 }}><ArrowBackIcon /></IconButton>
        <Box>
          <Breadcrumbs>
            <Link underline="hover" color="inherit" sx={{ cursor: 'pointer' }} onClick={() => navigate('/')}>Проекты</Link>
            <Typography color="text.primary">{project.name}</Typography>
          </Breadcrumbs>
        </Box>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} variant="scrollable" scrollButtons="auto">
          <Tab label="3D Модель" />
          <Tab label="Структура" />
          <Tab label="Элементы" />
          <Tab label="Замечания" />
          <Tab label="Аналитика" />
          <Tab label="Контроль качества" />
          <Tab label="Отчёты и экспорт" />
        </Tabs>
      </Box>

      {tab === 0 && <ViewerTab projectId={projectId} />}
      {tab === 1 && <StructureTab projectId={projectId} buildings={project.buildings} />}
      {tab === 2 && <ElementsTab projectId={projectId} />}
      {tab === 3 && <IssuesTab projectId={projectId} />}
      {tab === 4 && <AnalyticsTab projectId={projectId} />}
      {tab === 5 && <QualityTab projectId={projectId} />}
      {tab === 6 && <ExportTab projectId={projectId} />}
    </Box>
  );
}
