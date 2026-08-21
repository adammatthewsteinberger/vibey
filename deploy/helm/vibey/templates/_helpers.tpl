{{- define "vibey.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "vibey.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "vibey.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "vibey.labels" -}}
app.kubernetes.io/name: {{ include "vibey.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
{{- end -}}

{{- define "vibey.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "vibey.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{/*
The DSN is the one piece of config that must never be assembled in two
places: an existing Secret wins outright, otherwise the built-in postgres
Service is addressed by its in-cluster DNS name.
*/}}
{{- define "vibey.dsnSecretName" -}}
{{- if .Values.dsn.existingSecret -}}
{{- .Values.dsn.existingSecret -}}
{{- else -}}
{{- printf "%s-dsn" (include "vibey.fullname" .) -}}
{{- end -}}
{{- end -}}

{{- define "vibey.dsnSecretKey" -}}
{{- if .Values.dsn.existingSecret -}}
{{- .Values.dsn.existingSecretKey -}}
{{- else -}}
dsn
{{- end -}}
{{- end -}}
