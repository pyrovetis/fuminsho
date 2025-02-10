def main(request):
    path = request.path
    canonical_path = request.build_absolute_uri(path)
    return {"path": path, "canonical_path": canonical_path}
