class ResponseRenderers():
  def render(data, status, errorMessage):
    return {
      'result': data,
      'resultCode': status,
      'message': errorMessage,
    }

  def renderList(data, total, status, errorMessage,):
    return {
      'result': data,
      'total': total,
      'resultCode': status,
      'message': errorMessage,
    }