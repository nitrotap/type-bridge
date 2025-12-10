"""Tests for function generation support."""

from __future__ import annotations

import tempfile
from pathlib import Path

from type_bridge.generator import generate_models, parse_tql_schema
from type_bridge.generator.render import render_functions


class TestParseFunctions:
    """Tests for function parsing."""

    def test_parse_simple_function(self) -> None:
        """Parse a simple function definition."""
        schema_text = """
            define

            fun calculate-age($birth-date: date) -> { int }:
                match
                    $p isa person, has birth-date $birth-date;
                return { 30 };
        """
        schema = parse_tql_schema(schema_text)

        assert "calculate-age" in schema.functions
        func = schema.functions["calculate-age"]
        assert func.name == "calculate-age"
        assert func.return_type == "int"
        assert len(func.parameters) == 1
        assert func.parameters[0].name == "birth-date"
        assert func.parameters[0].type == "date"

    def test_parse_multi_arg_function(self) -> None:
        """Parse a function with multiple arguments."""
        schema_text = """
            define

            fun risk-score($age: int, $income: double) -> { double }:
                match
                    ...
                return { 0.5 };
        """
        schema = parse_tql_schema(schema_text)

        assert "risk-score" in schema.functions
        func = schema.functions["risk-score"]
        assert len(func.parameters) == 2
        assert func.parameters[0].name == "age"
        assert func.parameters[0].type == "int"
        assert func.parameters[1].name == "income"
        assert func.parameters[1].type == "double"


class TestRenderFunctions:
    """Tests for function rendering."""

    def test_render_simple_function(self) -> None:
        """Render a simple function wrapper."""
        schema_text = """
            define
            fun calculate-age($birth-date: date) -> { int }:
                return { 1 };
        """
        schema = parse_tql_schema(schema_text)
        source = render_functions(schema)

        assert "def calculate_age(birth_date: date | Expression) -> FunctionCallExpr:" in source
        assert 'return FunctionCallExpr("calculate-age", [birth_date])' in source
        assert "from datetime import date" in source
        assert "from type_bridge.expressions import Expression, FunctionCallExpr" in source

    def test_render_multi_arg_function(self) -> None:
        """Render function with multiple arguments."""
        schema_text = """
            define
            fun risk-score($age: int, $income: double) -> { double }:
                return { 1.0 };
        """
        schema = parse_tql_schema(schema_text)
        source = render_functions(schema)

        assert "def risk_score(age: int | Expression, income: float | Expression) -> FunctionCallExpr:" in source
        assert 'return FunctionCallExpr("risk-score", [age, income])' in source


class TestGenerateFunctions:
    """Tests for full generation pipeline including functions."""

    def test_generates_functions_file(self) -> None:
        """Generate package with functions.py."""
        schema_text = """
            define
            fun calculate-age($birth-date: date) -> { int }:
                return { 1 };

            entity person, owns age @key;
            attribute age, value int;
        """

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "models"
            generate_models(schema_text, output)

            # Check functions.py exists
            assert (output / "functions.py").exists()
            assert (output / "__init__.py").exists()

            # Check __init__.py exports functions
            init_content = (output / "__init__.py").read_text()
            assert "from . import attributes, entities, relations, functions" in init_content
            assert '"functions",' in init_content

            # Check content compiles
            functions_content = (output / "functions.py").read_text()
            compile(functions_content, "functions.py", "exec")

    def test_skips_functions_file_if_none(self) -> None:
        """Do not generate functions.py if no functions in schema."""
        schema_text = """
            define
            entity person, owns age @key;
            attribute age, value int;
        """

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "models"
            generate_models(schema_text, output)

            assert not (output / "functions.py").exists()
            init_content = (output / "__init__.py").read_text()
            assert "functions" not in init_content
