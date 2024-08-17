from aws_cdk import (
    Stack,
    aws_codepipeline as codepipeline,
    pipelines as pipelines,
    aws_secretsmanager as secretsmanager,
    aws_codepipeline as codepipeline,
    aws_codebuild as codebuild,
    aws_codepipeline_actions as codepipeline_actions,
    CfnOutput,
    SecretValue
)
from constructs import Construct

class MyPipelineStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        # Obtener el secreto de GitHub desde Secrets Manager
        github_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "GitHubToken", "github_token"
        )

        
        pipeline = codepipeline.Pipeline(
            self, 'CICD_Pipeline',
            cross_account_keys = False
        )


        # Crear el pipeline
        repo = pipelines.CodePipeline(
            self, "Pipeline",
            synth=pipelines.ShellStep("Synth",
                input=pipelines.CodePipelineSource.git_hub(
                    "0lb4p/cicd-workshop-aws",  # Reemplaza con tu usuario/repositorio de GitHub
                    "main",  # Reemplaza con la rama que deseas usar
                    authentication=SecretValue.secrets_manager("github_token", json_field='github/token')
                ),
                commands=[
                    "npm install -g aws-cdk",  # Instalar CDK
                    "pip install -r requirements.txt",  # Instalar dependencias
                    "npx cdk synth"  # Sintetizar la app de CDK
                ]
            )
        )


        code_quality_build = codebuild.PipelineProject(
            self, 'CodeQualityBuild',
            build_spec = codebuild.BuildSpec.from_object({
                'version': '0.2',
                           }),
            environment = codebuild.BuildEnvironment(
                build_image = codebuild.LinuxBuildImage.STANDARD_5_0,
                privileged = True,
                compute_type = codebuild.ComputeType.LARGE,
            ),
        )

        source_output = codepipeline.Artifact()
        unit_test_output = codepipeline.Artifact()

        source_action = codepipeline_actions.CodeCommitSourceAction(
            action_name = 'CodeCommit',
            repository = repo,
            output = source_output,
            branch = 'main'
        )

        pipeline.add_stage(
            stage_name = 'Source',
            actions = [repo]
        )

        build_action = codepipeline_actions.CodeBuildAction(
            action_name = 'Unit-Test',
            project = code_quality_build,
            input = source_output,  # The build action must use the CodeCommitSourceAction output as input.
            outputs = [unit_test_output]
        )

        pipeline.add_stage(
            stage_name = 'Code-Quality-Testing',
            actions = [build_action]
        )

        CfnOutput(
            self, 'CodeCommitRepositoryUrl',
            value = f"https://github.com/0lb4p/cicd-workshop-aws.git"
        )
