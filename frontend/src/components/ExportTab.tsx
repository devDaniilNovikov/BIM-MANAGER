import { useState } from 'react';
import {
  Box, Button, Card, CardContent, Grid, Typography, MenuItem,
  TextField, Stack, Divider,
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import DescriptionIcon from '@mui/icons-material/Description';
import TableChartIcon from '@mui/icons-material/TableChart';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import { getExportUrl, type ReportType, type ExportFormat } from '../api/export';

interface Props { projectId: string; }

const reports: { type: ReportType; label: string; desc: string }[] = [
  { type: 'spaces', label: 'Ведомость помещений', desc: 'Список помещений с площадями и объёмами' },
  { type: 'doors-windows', label: 'Ведомость дверей и окон', desc: 'Перечень дверей и оконных проёмов' },
  { type: 'walls', label: 'Ведомость стен', desc: 'Стены с параметрами и материалами' },
  { type: 'slabs', label: 'Ведомость перекрытий', desc: 'Плиты перекрытий с характеристиками' },
  { type: 'quantities', label: 'Сводная таблица количеств', desc: 'Количественные показатели по категориям' },
  { type: 'summary', label: 'Аналитический отчёт', desc: 'Сводный отчёт по проекту' },
  { type: 'issues', label: 'Журнал замечаний', desc: 'Перечень всех замечаний по модели' },
];

const formatIcon = (f: ExportFormat) => {
  if (f === 'pdf') return <PictureAsPdfIcon />;
  if (f === 'xlsx') return <TableChartIcon />;
  return <DescriptionIcon />;
};

export default function ExportTab({ projectId }: Props) {
  const [format, setFormat] = useState<ExportFormat>('xlsx');

  const download = (type: ReportType) => {
    window.open(getExportUrl(projectId, type, format), '_blank');
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">Отчёты и экспорт</Typography>
        <TextField select size="small" label="Формат" value={format} onChange={e => setFormat(e.target.value as ExportFormat)} sx={{ minWidth: 120 }}>
          <MenuItem value="xlsx">Excel (.xlsx)</MenuItem>
          <MenuItem value="csv">CSV (.csv)</MenuItem>
          <MenuItem value="pdf">PDF (.pdf)</MenuItem>
        </TextField>
      </Box>

      <Grid container spacing={2}>
        {reports.map(r => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={r.type}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography variant="h6" gutterBottom>{r.label}</Typography>
                <Typography variant="body2" color="text.secondary">{r.desc}</Typography>
              </CardContent>
              <Divider />
              <Box sx={{ p: 2 }}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={formatIcon(format)}
                  endIcon={<DownloadIcon />}
                  onClick={() => download(r.type)}
                >
                  Скачать {format.toUpperCase()}
                </Button>
              </Box>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
