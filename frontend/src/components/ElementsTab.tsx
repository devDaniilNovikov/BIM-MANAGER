import { useEffect, useState, useCallback } from 'react';
import {
  Box, TextField, MenuItem, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, Typography, Chip, Pagination, LinearProgress,
  InputAdornment, Dialog, DialogTitle, DialogContent, IconButton, Stack,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import CloseIcon from '@mui/icons-material/Close';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import { getElements, getElement, getElementClasses } from '../api/elements';
import type { Element, ElementDetail } from '../types';
import { SEVERITY_RU, STATUS_RU, translateIfcClass, translateMessage, t } from '../utils/translations';

interface Props {
  projectId: string;
}

export default function ElementsTab({ projectId }: Props) {
  const [items, setItems] = useState<Element[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [classes, setClasses] = useState<{ ifc_class: string; count: number }[]>([]);
  const [filterClass, setFilterClass] = useState('');
  const [search, setSearch] = useState('');
  const [hasIssues, setHasIssues] = useState('');
  const [detail, setDetail] = useState<ElementDetail | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const pageSize = 50;

  useEffect(() => {
    getElementClasses(projectId).then(r => setClasses(r.data));
  }, [projectId]);

  const load = useCallback(() => {
    setLoading(true);
    getElements(projectId, {
      ifc_class: filterClass || undefined,
      search: search || undefined,
      has_issues: hasIssues === '' ? undefined : hasIssues === 'true',
      page,
      page_size: pageSize,
    }).then(r => {
      setItems(r.data.items);
      setTotal(r.data.total);
    }).finally(() => setLoading(false));
  }, [projectId, filterClass, search, hasIssues, page]);

  useEffect(load, [load]);

  const openDetail = async (el: Element) => {
    const r = await getElement(projectId, el.id);
    setDetail(r.data);
    setDetailOpen(true);
  };

  const fmt = (v: number | null) => v != null ? v.toFixed(2) : '—';

  return (
    <Box>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 2 }}>
        <TextField
          size="small"
          placeholder="Поиск по имени, типу, GUID..."
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1); }}
          InputProps={{ startAdornment: <InputAdornment position="start"><SearchIcon /></InputAdornment> }}
          sx={{ minWidth: 250 }}
        />
        <TextField
          select size="small" label="Класс IFC" value={filterClass}
          onChange={e => { setFilterClass(e.target.value); setPage(1); }}
          sx={{ minWidth: 180 }}
        >
          <MenuItem value="">Все классы</MenuItem>
          {classes.map(c => (
            <MenuItem key={c.ifc_class} value={c.ifc_class}>{translateIfcClass(c.ifc_class)} ({c.count})</MenuItem>
          ))}
        </TextField>
        <TextField
          select size="small" label="Проблемные" value={hasIssues}
          onChange={e => { setHasIssues(e.target.value); setPage(1); }}
          sx={{ minWidth: 160 }}
        >
          <MenuItem value="">Все</MenuItem>
          <MenuItem value="true">С замечаниями</MenuItem>
          <MenuItem value="false">Без замечаний</MenuItem>
        </TextField>
        <Typography variant="body2" color="text.secondary" sx={{ alignSelf: 'center' }}>
          Всего: {total}
        </Typography>
      </Stack>

      {loading && <LinearProgress sx={{ mb: 1 }} />}

      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Класс</TableCell>
              <TableCell>Наименование</TableCell>
              <TableCell>Тип</TableCell>
              <TableCell>Этаж</TableCell>
              <TableCell>Материал</TableCell>
              <TableCell align="right">Площадь</TableCell>
              <TableCell align="right">Объём</TableCell>
              <TableCell align="center">Статус</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map(el => (
              <TableRow
                key={el.id}
                hover
                sx={{ cursor: 'pointer', bgcolor: el.is_problematic ? 'rgba(255,152,0,0.05)' : undefined }}
                onClick={() => openDetail(el)}
              >
                <TableCell><Chip label={translateIfcClass(el.ifc_class)} size="small" /></TableCell>
                <TableCell>{el.name || '—'}</TableCell>
                <TableCell>{el.type_name || '—'}</TableCell>
                <TableCell>{el.storey_name || '—'}</TableCell>
                <TableCell sx={{ maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{el.material || '—'}</TableCell>
                <TableCell align="right">{fmt(el.area)}</TableCell>
                <TableCell align="right">{fmt(el.volume)}</TableCell>
                <TableCell align="center">
                  {el.is_problematic && <WarningAmberIcon color="warning" fontSize="small" />}
                </TableCell>
              </TableRow>
            ))}
            {items.length === 0 && !loading && (
              <TableRow><TableCell colSpan={8} align="center">Элементы не найдены</TableCell></TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {total > pageSize && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <Pagination count={Math.ceil(total / pageSize)} page={page} onChange={(_, v) => setPage(v)} />
        </Box>
      )}

      <Dialog open={detailOpen} onClose={() => setDetailOpen(false)} maxWidth="md" fullWidth>
        {detail && (
          <>
            <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
                <Typography variant="h6">{detail.name || detail.ifc_class}</Typography>
                <Typography variant="caption" color="text.secondary">{detail.global_id}</Typography>
              </Box>
              <IconButton onClick={() => setDetailOpen(false)}><CloseIcon /></IconButton>
            </DialogTitle>
            <DialogContent dividers>
              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">Класс IFC</Typography>
                  <Typography>{translateIfcClass(detail.ifc_class)}</Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">Тип</Typography>
                  <Typography>{detail.type_name || '—'}</Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">Этаж</Typography>
                  <Typography>{detail.storey_name || '—'}</Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">Помещение</Typography>
                  <Typography>{detail.space_name || '—'}</Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">Материал</Typography>
                  <Typography>{detail.material || '—'}</Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">Описание</Typography>
                  <Typography>{detail.description || '—'}</Typography>
                </Box>
              </Box>

              <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>Количественные характеристики</Typography>
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 2 }}>
                {[
                  ['Длина', detail.length], ['Ширина', detail.width], ['Высота', detail.height],
                  ['Площадь', detail.area], ['Объём', detail.volume], ['Масса', detail.weight],
                ].map(([label, val]) => (
                  <Box key={label as string}>
                    <Typography variant="subtitle2" color="text.secondary">{label as string}</Typography>
                    <Typography>{val != null ? (val as number).toFixed(3) : '—'}</Typography>
                  </Box>
                ))}
              </Box>

              <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>Полнота данных</Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {[
                  ['Имя', detail.has_name], ['Тип', detail.has_type], ['Этаж', detail.has_storey],
                  ['Материал', detail.has_material], ['Количества', detail.has_quantities],
                ].map(([label, val]) => (
                  <Chip
                    key={label as string}
                    label={label as string}
                    color={val ? 'success' : 'error'}
                    variant="outlined"
                    size="small"
                  />
                ))}
              </Box>

              {detail.issues.length > 0 && (
                <>
                  <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>Замечания ({detail.issues.length})</Typography>
                  {detail.issues.map(iss => (
                    <Box key={iss.id} sx={{ p: 1, mb: 1, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
                      <Box sx={{ display: 'flex', gap: 1, mb: 0.5 }}>
                        <Chip label={t(SEVERITY_RU, iss.severity)} size="small" color={iss.severity === 'error' ? 'error' : iss.severity === 'warning' ? 'warning' : 'info'} />
                        <Chip label={t(STATUS_RU, iss.status)} size="small" variant="outlined" />
                      </Box>
                      <Typography variant="body2">{translateMessage(iss.message)}</Typography>
                      {iss.recommendation && (
                        <Typography variant="body2" color="primary" sx={{ mt: 0.5 }}>{iss.recommendation}</Typography>
                      )}
                    </Box>
                  ))}
                </>
              )}

              {detail.properties_json && (() => {
                let parsed;
                try { parsed = JSON.parse(detail.properties_json); } catch { parsed = null; }
                return parsed ? (
                  <>
                    <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>Наборы свойств</Typography>
                    <Box sx={{ maxHeight: 300, overflow: 'auto', bgcolor: 'grey.50', p: 2, borderRadius: 1, fontSize: 13 }}>
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                        {JSON.stringify(parsed, null, 2)}
                      </pre>
                    </Box>
                  </>
                ) : null;
              })()}
            </DialogContent>
          </>
        )}
      </Dialog>
    </Box>
  );
}
