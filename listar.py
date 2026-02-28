"""Lista concursos coletados do seen.json."""

import json
import sys
import os

# Fix encoding on Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from config import SEEN_FILE


def listar(filtro_estado=None):
    if not os.path.exists(SEEN_FILE):
        print("Nenhum concurso coletado ainda.")
        return

    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        dados = json.load(f)

    if not dados:
        print("Nenhum concurso coletado ainda.")
        return

    # Agrupa por estado
    por_estado = {}
    for info in dados.values():
        estado = info.get("estado", "?")
        if filtro_estado and estado not in filtro_estado:
            continue
        por_estado.setdefault(estado, []).append(info)

    total = sum(len(v) for v in por_estado.values())
    print(f"\n{'=' * 60}")
    print(f"  CONCURSOS COLETADOS: {total} no total")
    print(f"{'=' * 60}")

    for estado in sorted(por_estado.keys()):
        concursos = por_estado[estado]
        print(f"\n--- {estado} ({len(concursos)} concursos) ---\n")

        for c in concursos:
            titulo = c.get("titulo", "?")
            vagas = c.get("vagas", "")
            salario = c.get("salario", "")
            escolaridade = c.get("escolaridade", "")
            cargos = c.get("cargos", "")
            prazo = c.get("prazo_inscricao", "")
            url = c.get("url", "")
            edital = c.get("url_edital", "")

            print(f"  {titulo}")
            if vagas or salario:
                info = f"    {vagas} vagas" if vagas else "    "
                if salario:
                    info += f" | Ate {salario}"
                print(info)
            if escolaridade:
                print(f"    Nivel: {escolaridade}")
            if cargos:
                print(f"    Cargos: {cargos}")
            if prazo:
                print(f"    Inscricoes ate: {prazo}")
            if edital:
                print(f"    Edital: {edital}")
            if url:
                print(f"    Detalhes: {url}")
            print()

    print(f"{'=' * 60}")


if __name__ == "__main__":
    filtro = None
    if len(sys.argv) > 1:
        filtro = [s.upper() for s in sys.argv[1:]]
        print(f"Filtrando por: {', '.join(filtro)}")
    listar(filtro)
