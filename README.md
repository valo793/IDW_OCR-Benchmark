# OCR Import Documents Synthetic Dataset Generator

Mini-projeto Python para gerar documentos sintéticos de importação para benchmark de OCR.

Tipos de documentos gerados:
- DI
- DUIMP
- DDI
- CTAC

O gerador cria:
- PDFs sintéticos com layout documental
- imagens PNG limpas
- variações degradadas para simular baixa qualidade
- ground truth em CSV e XLSX
- template de benchmark para preencher resultados dos OCRs
- script de avaliação de métricas

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

No Linux/Mac:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Gerar dataset

```bash
python src/generate_dataset.py --docs-per-type 20 --output ./dataset
```

Isso gera 80 documentos base, sendo 20 para cada tipo, e suas variações de qualidade.

## Gerar dataset menor para teste

```bash
python src/generate_dataset.py --docs-per-type 3 --output ./dataset_teste
```

## Estrutura de saída

```text
dataset/
  01_pdfs/
  02_images_clean/
  03_images_degraded/
  04_ground_truth/
  05_benchmark/
```

## Como usar no estudo

1. Rode o gerador.
2. Use as imagens em `03_images_degraded` em diferentes OCRs.
3. Preencha o arquivo `benchmark_template.xlsx` com os valores extraídos por OCR.
4. Rode o script de avaliação:

```bash
python src/evaluate_benchmark.py --input ./dataset/05_benchmark/benchmark_template.xlsx --output ./dataset/05_benchmark/metrics_output.xlsx
```

## Observação importante

Todos os dados são sintéticos. Não use dados reais de clientes, importadores, processos ou documentos fiscais sem autorização e anonimização formal.
