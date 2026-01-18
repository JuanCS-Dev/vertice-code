import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd() / "src"))

from vertice_tui.core.autoaudit.logger import BlackBoxLogger  # noqa: E402


def test_logger_paths():
    print("🧪 Verificando BlackBoxLogger Autosave...")

    # Instantiate logger
    logger = BlackBoxLogger()
    print(f"📂 Output Directory configurado: {logger.output_dir}")

    # Verify it is absolute
    if not logger.output_dir.is_absolute():
        print("❌ ERRO: Caminho não é absoluto!")
        return

    # Verify it is inside the project (sanity check)
    cwd = Path.cwd()
    if str(cwd) not in str(logger.output_dir):
        print(
            f"⚠️ AVISO: Output dir ({logger.output_dir}) não parece estar dentro do CWD ({cwd}). Isso pode ser normal se o script rodar de outro lugar, mas vale checar."
        )

    # Attempt to save a file
    dummy_report = {"status": "TEST_OK", "message": "Validating autosave fix"}

    try:
        saved_path = logger.save_report(dummy_report)
        print(f"✅ Arquivo salvo com sucesso: {saved_path}")

        # Verify file exists
        path_obj = Path(saved_path)
        if path_obj.exists():
            print("✅ Verificação de disco: O arquivo REALMENTE existe.")
            # Clean up
            path_obj.unlink()
            print("🧹 Arquivo de teste removido.")
        else:
            print("❌ ERRO CRÍTICO: save_report retornou sucesso mas arquivo não está no disco!")

    except Exception as e:
        print(f"❌ Exceção ao salvar: {e}")


if __name__ == "__main__":
    test_logger_paths()
