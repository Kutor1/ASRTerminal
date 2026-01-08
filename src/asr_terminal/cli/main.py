"""
Command Line Interface for ASR Terminal.
"""
import asyncio
import click
from pathlib import Path
from typing import Optional
from ..service import ASRService
from ..config.manager import ConfigManager
from ..utils.logger import setup_logging, get_logger
from ..engines import EngineFactory

logger = get_logger(__name__)


@click.group()
@click.version_option(version="1.0.0")
@click.option('--config', '-c', default='config/config.yaml', help='Path to config file')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.pass_context
def cli(ctx, config: str, debug: bool):
    """
    ASR Terminal - Multi-Engine Speech Recognition Tool

    Supports real-time and batch speech recognition with multiple engines.
    """
    # Setup logging
    log_level = "DEBUG" if debug else "INFO"
    setup_logging(log_level)

    # Load configuration
    try:
        config_manager = ConfigManager(config)
    except Exception as e:
        click.echo(f"Error loading config: {e}", err=True)
        ctx.exit(1)

    # Initialize service
    service = ASRService(config_manager)

    # Store in context
    ctx.ensure_object(dict)
    ctx.obj['service'] = service
    ctx.obj['config'] = config_manager


@cli.command()
@click.argument('file_paths', nargs=-1, type=click.Path(exists=True))
@click.option('--engine', '-e', help='Recognition engine to use')
@click.option('--language', '-l', help='Language code (e.g., zh, en)')
@click.option('--output', '-o', help='Output directory')
@click.option('--format', '-f', multiple=True,
              type=click.Choice(['txt', 'srt', 'json']),
              default=['txt'], help='Output format(s)')
@click.option('--workers', '-w', default=4, help='Number of concurrent workers')
@click.pass_context
def batch(ctx, file_paths, engine, language, output, format, workers):
    """
    Batch recognize audio files.

    Examples:

        \b
        # Single file
        asr batch audio.wav

        \b
        # Multiple files with Whisper
        asr batch audio1.wav audio2.mp3 -e whisper -l zh

        \b
        # Export to multiple formats
        asr batch *.wav -f txt -f srt -o ./output

        \b
        # Use 8 concurrent workers
        asr batch *.wav -w 8
    """
    service = ctx.obj['service']
    config = ctx.obj['config']

    if not file_paths:
        click.echo("Error: No files specified", err=True)
        ctx.exit(1)

    async def run():
        try:
            # Initialize service
            engine_name = engine or config.get('engine.default')
            await service.initialize(engine_name)

            # Update output config
            if output:
                config.set('output.export.directory', output)
            if format:
                config.set('output.export.formats', list(format))

            # Process files
            results = await service.recognize_files_batch(
                file_paths=file_paths,
                language=language,
                max_workers=workers
            )

            # Summary
            click.echo(f"\n✓ Completed! Processed {len(results)} file(s)")

        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            logger.error(f"Batch processing failed: {e}")
            ctx.exit(1)
        finally:
            await service.cleanup()

    asyncio.run(run())


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--engine', '-e', help='Recognition engine to use')
@click.option('--language', '-l', help='Language code (e.g., zh, en)')
@click.option('--output', '-o', help='Output directory')
@click.option('--format', '-f', multiple=True,
              type=click.Choice(['txt', 'srt', 'json']),
              default=['txt'], help='Output format(s)')
@click.pass_context
def transcribe(ctx, file_path, engine, language, output, format):
    """
    Transcribe a single audio file.

    Examples:

        \b
        asr transcribe audio.wav

        \b
        # With specific engine and language
        asr transcribe audio.wav -e whisper -l zh

        \b
        # Export to SRT subtitle format
        asr transcribe audio.wav -f srt
    """
    service = ctx.obj['service']
    config = ctx.obj['config']

    async def run():
        try:
            # Initialize service
            engine_name = engine or config.get('engine.default')
            await service.initialize(engine_name)

            # Update output config
            if output:
                config.set('output.export.directory', output)
            if format:
                config.set('output.export.formats', list(format))

            # Process file
            transcript = await service.recognize_file(
                file_path=file_path,
                language=language
            )

            click.echo(f"\n✓ Transcription completed: {file_path}")

        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            logger.error(f"Transcription failed: {e}")
            ctx.exit(1)
        finally:
            await service.cleanup()

    asyncio.run(run())


@cli.command()
@click.pass_context
def list_engines(ctx):
    """List all available recognition engines."""
    engines = EngineFactory.list_engines()

    click.echo("Available engines:")
    for engine in engines:
        click.echo(f"  • {engine}")

    click.echo(f"\nTotal: {len(engines)} engine(s)")


@cli.command()
@click.pass_context
def config_info(ctx):
    """Show current configuration."""
    config = ctx.obj['config']

    click.echo("Current Configuration:")
    click.echo(f"  Default engine: {config.get('engine.default')}")
    click.echo(f"  Sample rate: {config.get('audio.sample_rate')} Hz")
    click.echo(f"  Output formats: {', '.join(config.get('output.export.formats'))}")
    click.echo(f"  Output directory: {config.get('output.export.directory')}")


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == '__main__':
    main()
